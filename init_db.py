import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Blog posts table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS blog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        date_posted TEXT,
        media_type TEXT,
        media_file TEXT
    )
''')

# Team table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS team (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        bio TEXT,
        image TEXT
    )
''')

# Terminal uploads table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS terminal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        filename TEXT,
        filetype TEXT,
        uploader TEXT,
        date_uploaded TEXT
    )
''')

# Users (admin) table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')

# Comments table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        comment TEXT,
        date_posted TEXT,
        approved INTEGER DEFAULT 0
    )
''')

# Check if default admin already exists
cursor.execute("SELECT * FROM users WHERE username = 'admin'")
if not cursor.fetchone():
    hashed_password = generate_password_hash('admin123')
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password))
    print("✅ Default admin created (username: admin, password: admin123)")
else:
    print("⚠️  Admin user already exists.")

conn.commit()
conn.close()
print("✅ Database initialized.")
