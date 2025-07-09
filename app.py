# app.py (Version 7.0 - The Unified Core)

import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['DATABASE'] = 'genesis.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp3', 'mp4'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- DATABASE HELPERS ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS users;")
        cursor.execute("DROP TABLE IF EXISTS blog;")
        cursor.execute("DROP TABLE IF EXISTS team;")
        cursor.execute("DROP TABLE IF EXISTS terminal_files;")
        cursor.execute("DROP TABLE IF EXISTS qa_board;")
        cursor.execute("DROP TABLE IF EXISTS payment_methods;")
        cursor.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE blog (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL, date_posted TIMESTAMP NOT NULL, media_type TEXT, file_path TEXT, youtube_url TEXT);""")
        cursor.execute("""CREATE TABLE team (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE terminal_files (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, description TEXT NOT NULL);""")
        cursor.execute("""CREATE TABLE qa_board (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, question TEXT NOT NULL, answer TEXT, date_asked TIMESTAMP NOT NULL, date_answered TIMESTAMP, is_answered INTEGER NOT NULL DEFAULT 0);""")
        cursor.execute("""CREATE TABLE payment_methods (id INTEGER PRIMARY KEY AUTOINCREMENT, method_name TEXT NOT NULL, details TEXT NOT NULL, category TEXT NOT NULL CHECK(category IN ('Zambian', 'International')));""")
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?);", ('admin', generate_password_hash('password')))
        cursor.execute("INSERT INTO team (name, role) VALUES ('Lord Alpha', 'Founder & Lead Architect');")
        cursor.execute("INSERT INTO payment_methods (method_name, details, category) VALUES ('Airtel Money', '+260 97 XXX XXXX (Your Name)', 'Zambian');")
        cursor.execute("INSERT INTO payment_methods (method_name, details, category) VALUES ('PayPal', 'your.email@example.com', 'International');")
        db.commit()
        print("Database initialized successfully with ALL tables.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- LOGIN DECORATOR & CONTEXT PROCESSOR ---
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

# --- FRONTEND ROUTES ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/blog')
def blog():
    db = get_db()
    posts = db.execute('SELECT id, title, date_posted FROM blog ORDER BY date_posted DESC').fetchall()
    return render_template('blog.html', posts=posts)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    db = get_db()
    post = db.execute('SELECT * FROM blog WHERE id = ?', (post_id,)).fetchone()
    if not post: return "Post Not Found", 404
    return render_template('blog_post.html', post=post)

@app.route('/team')
def team():
    db = get_db()
    members = db.execute('SELECT * FROM team ORDER BY id').fetchall()
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
    zambian_methods = db.execute("SELECT * FROM payment_methods WHERE category = 'Zambian'").fetchall()
    international_methods = db.execute("SELECT * FROM payment_methods WHERE category = 'International'").fetchall()
    return render_template('support.html', zambian_methods=zambian_methods, international_methods=international_methods)

@app.route('/q-and-a', methods=['GET', 'POST'])
def q_and_a():
    db = get_db()
    if request.method == 'POST':
        username = request.form['username']
        question = request.form['question']
        db.execute('INSERT INTO qa_board (username, question, date_asked) VALUES (?, ?, ?)', (username, question, datetime.utcnow()))
        db.commit()
        flash('Your question has been submitted. The Genesis Team will respond shortly.', 'success')
        return redirect(url_for('q_and_a'))
    questions = db.execute('SELECT * FROM qa_board WHERE is_answered = 1 ORDER BY date_answered DESC').fetchall()
    return render_template('q_and_a.html', questions=questions)

# --- API ROUTES ---
@app.route('/api/terminal', methods=['POST'])
def api_terminal():
    command_str = request.json.get('command', '').lower().strip()
    parts = command_str.split()
    command = parts[0] if parts else ''
    args = parts[1:]
    output = ""
    db = get_db()
    if command == 'help':
        output = "COMMAND LIST:\n  help\n  ls\n  cat [file]\n  whoami\n  date\n  clear"
    elif command == 'ls':
        files = db.execute('SELECT filename FROM terminal_files').fetchall()
        output = '\n'.join([f['filename'] for f in files]) if files else "directory is empty"
    elif command == 'cat' and args:
        file_data = db.execute('SELECT description FROM terminal_files WHERE filename = ?', (args[0],)).fetchone()
        output = file_data['description'] if file_data else f"cat: {args[0]}: No such file"
    elif command == 'whoami':
        output = "root"
    elif command == 'date':
        output = datetime.now().strftime('%a %b %d %H:%M:%S UTC %Y')
    elif command:
        output = f"command not found: {command_str}"
    return jsonify({'output': output})

@app.route('/api/gbj', methods=['POST'])
def api_gbj():
    message = request.json.get('message', '').lower().strip()
    response = "I do not compute. My knowledge is limited. Ask 'help' for my functions."
    if 'who are you' in message:
        response = "I am GBJ, the Genesis Bionic Judge."
    elif 'hacking' in message:
        response = "Hacking is the art of creative problem-solving."
    elif 'python' in message:
        response = "Python is a high-level language, essential for automation."
    elif 'help' in message:
        response = "My functions involve queries on: 'hacking', 'python', and 'who are you'."
    return jsonify({'response': response})

# --- ADMIN SECTION ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
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

@app.route('/admin/blog', methods=['GET', 'POST'])
@login_required
def admin_blog():
    db = get_db()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        youtube_url = request.form.get('youtube_url')
        file = request.files.get('file')
        media_type, file_path = None, None
        if youtube_url:
            media_type = 'youtube'
        elif file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = os.path.join('uploads', filename)
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']: media_type = 'image'
            elif ext in ['mp4']: media_type = 'video'
            elif ext in ['mp3']: media_type = 'audio'
            elif ext in ['pdf']: media_type = 'pdf'
        db.execute('INSERT INTO blog (title, content, date_posted, media_type, file_path, youtube_url) VALUES (?, ?, ?, ?, ?, ?)',
                   (title, content, datetime.utcnow(), media_type, file_path, youtube_url))
        db.commit()
        flash('New blog post has been published.', 'success')
        return redirect(url_for('admin_blog'))
    posts = db.execute('SELECT id, title, date_posted FROM blog ORDER BY date_posted DESC').fetchall()
    return render_template('admin_blog.html', posts=posts)

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def admin_change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (session['user'],)).fetchone()
        if user and check_password_hash(user['password'], old_password):
            hashed_password = generate_password_hash(new_password)
            db.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_password, session['user']))
            db.commit()
            flash('Password updated successfully.', 'success')
        else:
            flash('Incorrect old password. Update failed.', 'error')
        return redirect(url_for('admin_change_password'))
    return render_template('admin_change_password.html')

@app.route('/admin/team', methods=['GET', 'POST'])
@login_required
def admin_team():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        db.execute('INSERT INTO team (name, role) VALUES (?, ?)', (name, role))
        db.commit()
        flash(f'Operative "{name}" added to the roster.', 'success')
        return redirect(url_for('admin_team'))
    team_members = db.execute('SELECT * FROM team ORDER BY id').fetchall()
    return render_template('admin_team.html', team_members=team_members)

@app.route('/admin/team/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_team_member(id):
    db = get_db()
    db.execute('DELETE FROM team WHERE id = ?', (id,))
    db.commit()
    flash('Operative removed from the roster.', 'info')
    return redirect(url_for('admin_team'))

@app.route('/admin/terminal-files', methods=['GET', 'POST'])
@login_required
def admin_terminal_files():
    db = get_db()
    if request.method == 'POST':
        filename = request.form['filename']
        description = request.form['description']
        db.execute('INSERT INTO terminal_files (filename, description) VALUES (?, ?)', (filename, description))
        db.commit()
        flash(f'File "{filename}" added to terminal.', 'success')
        return redirect(url_for('admin_terminal_files'))
    files = db.execute('SELECT * FROM terminal_files ORDER BY id').fetchall()
    return render_template('admin_terminal_files.html', files=files)

@app.route('/admin/terminal-files/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_terminal_file(id):
    db = get_db()
    db.execute('DELETE FROM terminal_files WHERE id = ?', (id,))
    db.commit()
    flash('Terminal file deleted.', 'info')
    return redirect(url_for('admin_terminal_files'))

@app.route('/admin/q-and-a')
@login_required
def admin_q_and_a():
    db = get_db()
    unanswered = db.execute('SELECT * FROM qa_board WHERE is_answered = 0 ORDER BY date_asked ASC').fetchall()
    answered = db.execute('SELECT * FROM qa_board WHERE is_answered = 1 ORDER BY date_answered DESC').fetchall()
    return render_template('admin_q_and_a.html', unanswered=unanswered, answered=answered)

@app.route('/admin/q-and-a/answer/<int:id>', methods=['POST'])
@login_required
def admin_answer_question(id):
    answer = request.form['answer']
    db = get_db()
    db.execute('UPDATE qa_board SET answer = ?, is_answered = 1, date_answered = ? WHERE id = ?', (answer, datetime.utcnow(), id))
    db.commit()
    flash('Answer has been published to the Q&A board.', 'success')
    return redirect(url_for('admin_q_and_a'))

@app.route('/admin/q-and-a/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_question(id):
    db = get_db()
    db.execute('DELETE FROM qa_board WHERE id = ?', (id,))
    db.commit()
    flash('Question has been deleted.', 'info')
    return redirect(url_for('admin_q_and_a'))

@app.route('/admin/payments', methods=['GET', 'POST'])
@login_required
def admin_payments():
    db = get_db()
    if request.method == 'POST':
        method_name = request.form['method_name']
        details = request.form['details']
        category = request.form['category']
        db.execute('INSERT INTO payment_methods (method_name, details, category) VALUES (?, ?, ?)',
                   (method_name, details, category))
        db.commit()
        flash(f'Payment method "{method_name}" added.', 'success')
        return redirect(url_for('admin_payments'))
    zambian_methods = db.execute("SELECT * FROM payment_methods WHERE category = 'Zambian'").fetchall()
    international_methods = db.execute("SELECT * FROM payment_methods WHERE category = 'International'").fetchall()
    return render_template('admin_payments.html', zambian_methods=zambian_methods, international_methods=international_methods)

@app.route('/admin/payments/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_payment(id):
    db = get_db()
    db.execute('DELETE FROM payment_methods WHERE id = ?', (id,))
    db.commit()
    flash('Payment method deleted.', 'info')
    return redirect(url_for('admin_payments'))

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)