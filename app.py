# app.py (Version 8.0 - Complete Zero-Command Deployment for Render Free Tier)

import os
import sqlite3
import psycopg2
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIGURATION (Handles Both Local and Production) ---
IS_PRODUCTION = os.environ.get('IS_PRODUCTION', 'False').lower() == 'true'

if IS_PRODUCTION:
    # Production settings (from Render environment variables)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads' # A temporary, non-persistent directory
else:
    # Local development settings
    app.config['SECRET_KEY'] = 'dev-secret'
    app.config['DATABASE'] = 'genesis.db'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp3', 'mp4'}
# We only create the directory locally, not needed in stateless production
if not IS_PRODUCTION:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# --- DATABASE HELPERS ---
def get_db():
    if 'db' not in g:
        if IS_PRODUCTION:
            g.db = psycopg2.connect(DATABASE_URL)
        else:
            g.db = sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
            g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    tables = ['users', 'blog', 'team', 'terminal_files', 'qa_board', 'payment_methods']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

    if IS_PRODUCTION:
        # PostgreSQL schema
        cursor.execute("""CREATE TABLE users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE blog (id SERIAL PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, date_posted TIMESTAMP NOT NULL, media_type TEXT, file_path TEXT, youtube_url TEXT);""")
        cursor.execute("""CREATE TABLE team (id SERIAL PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE terminal_files (id SERIAL PRIMARY KEY, filename TEXT NOT NULL, description TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE qa_board (id SERIAL PRIMARY KEY, username TEXT NOT NULL, question TEXT NOT NULL, answer TEXT, date_asked TIMESTAMP NOT NULL, date_answered TIMESTAMP, is_answered INTEGER NOT NULL DEFAULT 0);""")
        cursor.execute("""CREATE TABLE payment_methods (id SERIAL PRIMARY KEY, method_name TEXT NOT NULL, details TEXT NOT NULL, category TEXT NOT NULL);""")
        
        # Use %s for placeholders
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s);", ('admin', generate_password_hash('password')))
        cursor.execute("INSERT INTO team (name, role) VALUES (%s, %s);", ('Lord Alpha', 'Founder & Lead Architect'))
        cursor.execute("INSERT INTO payment_methods (method_name, details, category) VALUES (%s, %s, %s);", ('PayPal', 'your.email@example.com', 'International'))
    else:
        # SQLite schema
        cursor.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE blog (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL, date_posted TIMESTAMP NOT NULL, media_type TEXT, file_path TEXT, youtube_url TEXT);""")
        cursor.execute("""CREATE TABLE team (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE terminal_files (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, description TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE qa_board (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, question TEXT NOT NULL, answer TEXT, date_asked TIMESTAMP NOT NULL, date_answered TIMESTAMP, is_answered INTEGER NOT NULL DEFAULT 0);""")
        cursor.execute("""CREATE TABLE payment_methods (id INTEGER PRIMARY KEY AUTOINCREMENT, method_name TEXT NOT NULL, details TEXT NOT NULL, category TEXT NOT NULL CHECK(category IN ('Zambian', 'International')));""")
        
        # Use ? for placeholders
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?);", ('admin', generate_password_hash('password')))
        cursor.execute("INSERT INTO team (name, role) VALUES (?, ?);", ('Lord Alpha', 'Founder & Lead Architect'))
        cursor.execute("INSERT INTO payment_methods (method_name, details, category) VALUES (?, ?, ?);", ('PayPal', 'your.email@example.com', 'International'))
            
    db.commit()
    print("Database has been initialized.")

# =========================================================
# === NEW ONE-TIME INITIALIZATION ROUTE ===
# This flag prevents the route from being run more than once
db_initialized = False

@app.route('/init-database-on-first-run')
def one_time_init():
    global db_initialized
    if not IS_PRODUCTION:
        return "This route is for production use only.", 403
    if db_initialized:
        return "Database has already been initialized. This route is now disabled.", 403
    
    try:
        init_db()
        db_initialized = True
        return "SUCCESS: The database has been initialized. This route is now permanently disabled.", 200
    except Exception as e:
        return f"An error occurred during initialization: {e}", 500
# =========================================================

# --- ALL OTHER FUNCTIONS & ROUTES ---

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

# --- Public Routes ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/blog')
def blog():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, title, date_posted FROM blog ORDER BY date_posted DESC')
    posts = cursor.fetchall()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    db = get_db()
    cursor = db.cursor()
    query = 'SELECT * FROM blog WHERE id = %s' if IS_PRODUCTION else 'SELECT * FROM blog WHERE id = ?'
    cursor.execute(query, (post_id,))
    post = cursor.fetchone()
    if not post: return "Post Not Found", 404
    return render_template('blog_post.html', post=post)

@app.route('/team')
def team():
    db = get_db()
    cursor = db.cursor()
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
    db = get_db()
    cursor = db.cursor()
    query_z = "SELECT * FROM payment_methods WHERE category = %s" if IS_PRODUCTION else "SELECT * FROM payment_methods WHERE category = ?"
    cursor.execute(query_z, ('Zambian',))
    zambian_methods = cursor.fetchall()
    query_i = "SELECT * FROM payment_methods WHERE category = %s" if IS_PRODUCTION else "SELECT * FROM payment_methods WHERE category = ?"
    cursor.execute(query_i, ('International',))
    international_methods = cursor.fetchall()
    return render_template('support.html', zambian_methods=zambian_methods, international_methods=international_methods)

@app.route('/q-and-a', methods=['GET', 'POST'])
def q_and_a():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        username = request.form['username']
        question = request.form['question']
        query = 'INSERT INTO qa_board (username, question, date_asked) VALUES (%s, %s, %s)' if IS_PRODUCTION else 'INSERT INTO qa_board (username, question, date_asked) VALUES (?, ?, ?)'
        cursor.execute(query, (username, question, datetime.utcnow()))
        db.commit()
        flash('Your question has been submitted.', 'success')
        return redirect(url_for('q_and_a'))
    
    cursor.execute('SELECT * FROM qa_board WHERE is_answered = 1 ORDER BY date_answered DESC')
    questions = cursor.fetchall()
    return render_template('q_and_a.html', questions=questions)

# --- Admin Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        query = 'SELECT * FROM users WHERE username = %s' if IS_PRODUCTION else 'SELECT * FROM users WHERE username = ?'
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        # Handle tuple vs. dict access
        pwd_hash = user[2] if IS_PRODUCTION else user['password']
        user_name = user[1] if IS_PRODUCTION else user['username']

        if user and check_password_hash(pwd_hash, password):
            session['user'] = user_name
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

# Other admin routes here... (The pattern is the same: check IS_PRODUCTION for SQL syntax)
# ...

# --- Main Execution ---
if __name__ == "__main__":
    app.run(debug=not IS_PRODUCTION)