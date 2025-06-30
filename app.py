import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "genesis-secret-key")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "genesis123")

UPLOAD_FOLDER = 'static/uploads'
TEAM_FOLDER = os.path.join(UPLOAD_FOLDER, 'team')
ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEAM_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    projects = [
        {'title': 'WiFi Cracker', 'description': 'Brute-force WPA2 passwords.', 'image': 'wifi.png', 'link': '#'},
        {'title': 'Flask ChatBot', 'description': 'AI chatbot with Flask.', 'image': 'chatbot.png', 'link': '#'},
        {'title': 'Terminal Portfolio', 'description': 'Terminal-styled portfolio.', 'image': 'terminal.png', 'link': '#'}
    ]
    return render_template('projects.html', projects=projects)

@app.route('/skills')
def skills():
    skills = [
        {'name': 'Python', 'level': 90},
        {'name': 'Kali Linux', 'level': 85},
        {'name': 'Networking', 'level': 75},
        {'name': 'Exploitation', 'level': 80},
        {'name': 'Web Development', 'level': 70}
    ]
    return render_template('skills.html', skills=skills)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        with open('messages.txt', 'a') as f:
            f.write(f"From: {name} <{email}>\n{message}\n---\n")
        flash("Message received. Thanks!")
        return redirect('/contact')
    return render_template('contact.html')

@app.route('/terminal')
def terminal():
    return render_template('terminal.html')

@app.route('/tools')
def tools():
    tools = [
        {'name': 'Port Scanner', 'description': 'Scan open ports.', 'link': '#'},
        {'name': 'Hash Cracker', 'description': 'Crack hashes.', 'link': '#'},
        {'name': 'Payload Generator', 'description': 'Create reverse shells.', 'link': '#'},
        {'name': 'OSINT Tool', 'description': 'Public data recon.', 'link': '#'}
    ]
    return render_template('tools.html', tools=tools)

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if request.method == 'POST' and session.get('admin'):
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash('File uploaded.')
        else:
            flash('Invalid file type.')
        return redirect('/portfolio')
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('portfolio.html', files=files)

@app.route('/blog')
def blog():
    if os.path.exists('posts.json'):
        with open('posts.json', 'r') as f:
            posts = json.load(f)
    else:
        posts = []
    return render_template('blog.html', posts=posts)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/dashboard')
        flash('Invalid credentials.')
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect('/admin')
    return render_template('admin_dashboard.html')

@app.route('/admin/change', methods=['GET', 'POST'])
def change_credentials():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        new_user = request.form['username']
        new_pass = request.form['password']
        with open('.env', 'w') as f:
            f.write(f'ADMIN_USERNAME={new_user}\nADMIN_PASSWORD={new_pass}\nSECRET_KEY={app.secret_key}')
        flash('Credentials updated. Restart required.')
        return redirect('/dashboard')
    return render_template('admin_change.html')

@app.route('/admin/blog', methods=['GET', 'POST'])
def admin_blog():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')
        filename = ''
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
        posts = []
        if os.path.exists('posts.json'):
            with open('posts.json', 'r') as f:
                posts = json.load(f)
        posts.append({'title': title, 'content': content, 'file': filename})
        with open('posts.json', 'w') as f:
            json.dump(posts, f, indent=4)
        flash('Post added.')
        return redirect('/admin/blog')
    with open('posts.json', 'r') as f:
        posts = json.load(f)
    return render_template('admin_blog.html', posts=posts)

@app.route('/admin/delete/<int:post_id>')
def delete_post(post_id):
    if not session.get('admin'):
        return redirect('/admin')
    with open('posts.json', 'r') as f:
        posts = json.load(f)
    if 0 <= post_id < len(posts):
        posts.pop(post_id)
        with open('posts.json', 'w') as f:
            json.dump(posts, f, indent=4)
        flash('Post deleted.')
    return redirect('/admin/blog')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/team')
def team():
    with open('data/team.json', 'r') as f:
        members = json.load(f)
    with open('data/achievements.json', 'r') as f:
        achievements = json.load(f)
    return render_template('team.html', team=members, achievements=achievements)

@app.route('/admin/team', methods=['GET', 'POST'])
def admin_team():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        bio = request.form.get('bio', '')
        file = request.files.get('image')
        filename = ''
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(TEAM_FOLDER, filename))
        with open('data/team.json', 'r') as f:
            members = json.load(f)
        members.append({'name': name, 'role': role, 'bio': bio, 'image': filename})
        with open('data/team.json', 'w') as f:
            json.dump(members, f, indent=4)
        flash('Team member added.')
        return redirect('/admin/team')
    return render_template('admin_team.html')

@app.route('/admin/achievements', methods=['GET', 'POST'])
def admin_achievements():
    if not session.get('admin'):
        return redirect('/admin')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files.get('media')
        filename = ''
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(TEAM_FOLDER, filename))
        with open('data/achievements.json', 'r') as f:
            achievements = json.load(f)
        achievements.append({'title': title, 'description': description, 'media': filename})
        with open('data/achievements.json', 'w') as f:
            json.dump(achievements, f, indent=4)
        flash('Achievement added.')
        return redirect('/admin/achievements')
    return render_template('admin_achievements.html')

if __name__ == '__main__':
    app.run(debug=True)
