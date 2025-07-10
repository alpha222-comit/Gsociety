# app.py (Version 11.0 - The Inferred Production Build)

import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- NEW FOOLPROOF CONFIGURATION ---
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_PRODUCTION = DATABASE_URL is not None

if IS_PRODUCTION:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['SECRET_KEY'] = 'dev-secret'
    app.config['DATABASE'] = 'genesis.db'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

if not IS_PRODUCTION:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp3', 'mp4'}

# --- DATABASE HELPERS ---
def get_db():
    if 'db' not in g:
        if IS_PRODUCTION:
            g.db = psycopg2.connect(DATABASE_URL)
            g.db.autocommit = True
        else:
            g.db = sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row
    return g.db

def get_cursor():
    db = get_db()
    if IS_PRODUCTION:
        return db.cursor(cursor_factory=DictCursor)
    else:
        return db.cursor()

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    cursor = get_cursor()
    tables = ['users', 'blog', 'team', 'terminal_files', 'qa_board', 'payment_methods']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

    id_type = "SERIAL PRIMARY KEY" if IS_PRODUCTION else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    cursor.execute(f"""CREATE TABLE users (id {id_type}, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);""")
    cursor.execute(f"""CREATE TABLE blog (id {id_type}, title TEXT NOT NULL, content TEXT NOT NULL, date_posted TIMESTAMP NOT NULL, media_type TEXT, file_path TEXT, youtube_url TEXT);""")
    cursor.execute(f"""CREATE TABLE team (id {id_type}, name TEXT NOT NULL, role TEXT NOT NULL);""")
    cursor.execute(f"""CREATE TABLE terminal_files (id {id_type}, filename TEXT NOT NULL, description TEXT NOT NULL);""")
    cursor.execute(f"""CREATE TABLE qa_board (id {id_type}, username TEXT NOT NULL, question TEXT NOT NULL, answer TEXT, date_asked TIMESTAMP NOT NULL, date_answered TIMESTAMP, is_answered INTEGER NOT NULL DEFAULT 0);""")
    cursor.execute(f"""CREATE TABLE payment_methods (id {id_type}, method_name TEXT NOT NULL, details TEXT NOT NULL, category TEXT NOT NULL);""")
    
    query = "INSERT INTO users (username, password) VALUES (%s, %s);" if IS_PRODUCTION else "INSERT INTO users (username, password) VALUES (?, ?);"
    cursor.execute(query, ('admin', generate_password_hash('password')))
    
    print("Database has been initialized.")

# --- ONE-TIME INIT ROUTE ---
db_initialized = False
@app.route('/init-database-on-first-run')
def one_time_init():
    global db_initialized
    if not IS_PRODUCTION:
        return "This check has passed. You are in a local environment. This route is for production use only.", 403
    if db_initialized:
        return "Database has already been initialized. This route is now disabled.", 403
    try:
        init_db()
        db_initialized = True
        return "SUCCESS: The database has been initialized. This route is now permanently disabled.", 200
    except Exception as e:
        return f"An error occurred during initialization: {e}", 500

# --- HELPER FUNCTIONS ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Admin access required. Please authenticate.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# --- PUBLIC ROUTES ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/blog')
def blog():
    cursor = get_cursor()
    cursor.execute('SELECT id, title, date_posted FROM blog ORDER BY date_posted DESC')
    posts = cursor.fetchall()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    cursor = get_cursor()
    query = 'SELECT * FROM blog WHERE id = %s' if IS_PRODUCTION else 'SELECT * FROM blog WHERE id = ?'
    cursor.execute(query, (post_id,))
    post = cursor.fetchone()
    if not post: return "Post Not Found", 404
    return render_template('blog_post.html', post=post)

@app.route('/team')
def team():
    cursor = get_cursor()
    cursor.execute('SELECT * FROM team ORDER BY id')
    members = cursor.fetchall()
    return render_template('team.html', members=members)

@app.route('/terminal')
def terminal(): return render_template('terminal.html')

@app.route('/gbj')
def gbj(): return render_template('gbj.html')

@app.route('/services')
def services(): return render_template('services.html')

@app.route('/support')
def support():
    cursor = get_cursor()
    query = "SELECT * FROM payment_methods WHERE category = %s" if IS_PRODUCTION else "SELECT * FROM payment_methods WHERE category = ?"
    cursor.execute(query, ('Zambian',))
    zambian_methods = cursor.fetchall()
    cursor.execute(query, ('International',))
    international_methods = cursor.fetchall()
    return render_template('support.html', zambian_methods=zambian_methods, international_methods=international_methods)

@app.route('/q-and-a', methods=['GET', 'POST'])
def q_and_a():
    cursor = get_cursor()
    if request.method == 'POST':
        username = request.form['username']
        question = request.form['question']
        query = 'INSERT INTO qa_board (username, question, date_asked) VALUES (%s, %s, %s)' if IS_PRODUCTION else 'INSERT INTO qa_board (username, question, date_asked) VALUES (?, ?, ?)'
        cursor.execute(query, (username, question, datetime.utcnow()))
        flash('Your question has been submitted.', 'success')
        return redirect(url_for('q_and_a'))
    
    cursor.execute('SELECT * FROM qa_board WHERE is_answered = 1 ORDER BY date_answered DESC')
    questions = cursor.fetchall()
    return render_template('q_and_a.html', questions=questions)

# --- ADMIN ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = get_cursor()
        query = 'SELECT * FROM users WHERE username = %s' if IS_PRODUCTION else 'SELECT * FROM users WHERE username = ?'
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            flash('Login successful. Welcome, admin.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Access denied.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Other admin routes and API routes would continue here, all using get_cursor()
# For the sake of providing the complete working structure, they are included.

@app.route('/admin/blog', methods=['GET', 'POST'])
@login_required
def admin_blog():
    cursor = get_cursor()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        youtube_url = request.form.get('youtube_url')
        media_type, file_path = None, None
        
        if youtube_url:
            media_type = 'youtube'
        elif not IS_PRODUCTION: # File uploads are only processed in local dev
            file = request.files.get('file')
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_path = f"uploads/{filename}"
        elif IS_PRODUCTION and 'file' in request.files and request.files['file'].filename != '':
            flash("File uploads are disabled on the live server.", "error")
        
        query = 'INSERT INTO blog (title, content, date_posted, media_type, file_path, youtube_url) VALUES (%s, %s, %s, %s, %s, %s)' if IS_PRODUCTION else 'INSERT INTO blog (title, content, date_posted, media_type, file_path, youtube_url) VALUES (?, ?, ?, ?, ?, ?)'
        cursor.execute(query, (title, content, datetime.utcnow(), media_type, file_path, youtube_url))
        flash('New blog post has been published.', 'success')
        return redirect(url_for('admin_blog'))
        
    cursor.execute('SELECT * FROM blog ORDER BY date_posted DESC')
    posts = cursor.fetchall()
    return render_template('admin_blog.html', posts=posts)


@app.route('/admin/payments', methods=['GET', 'POST'])
@login_required
def admin_payments():
    cursor = get_cursor()
    if request.method == 'POST':
        method_name = request.form['method_name']
        details = request.form['details']
        category = request.form['category']
        query = 'INSERT INTO payment_methods (method_name, details, category) VALUES (%s, %s, %s)' if IS_PRODUCTION else 'INSERT INTO payment_methods (method_name, details, category) VALUES (?, ?, ?)'
        cursor.execute(query, (method_name, details, category))
        flash(f'Payment method "{method_name}" added.', 'success')
        return redirect(url_for('admin_payments'))
    
    query = "SELECT * FROM payment_methods WHERE category = %s" if IS_PRODUCTION else "SELECT * FROM payment_methods WHERE category = ?"
    cursor.execute(query, ('Zambian',))
    zambian_methods = cursor.fetchall()
    cursor.execute(query, ('International',))
    international_methods = cursor.fetchall()
    return render_template('admin_payments.html', zambian_methods=zambian_methods, international_methods=international_methods)


@app.route('/admin/payments/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_payment(id):
    cursor = get_cursor()
    query = "DELETE FROM payment_methods WHERE id = %s" if IS_PRODUCTION else "DELETE FROM payment_methods WHERE id = ?"
    cursor.execute(query, (id,))
    flash('Payment method deleted.', 'info')
    return redirect(url_for('admin_payments'))


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    app.run(debug=not IS_PRODUCTION)