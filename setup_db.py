import sqlite3
from werkzeug.security import generate_password_hash

def setup_database():
    conn = sqlite3.connect('genesis.db')
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

    # Insert sample terminal data only if empty
    cursor.execute('SELECT COUNT(*) FROM terminal')
    count = cursor.fetchone()[0]

    if count == 0:
        sample_terminal_data = [
            ("Linux Uploader", "Sample MP3 Upload", "sample_audio.mp3", "mp3", "admin", "2025-07-06"),
            ("Network Tool", "Packet Sniffer Simulation", "sniffer_sim.py", "code", "admin", "2025-07-06"),
            ("Exploit Demo", "Basic exploit POC script", "exploit_demo.py", "code", "admin", "2025-07-06"),
            ("Video Log", "Genesis Terminal intro", "terminal_intro.mp4", "mp4", "admin", "2025-07-06"),
            ("PDF Tool", "How to use Genesis", "manual.pdf", "pdf", "admin", "2025-07-06")
        ]
        cursor.executemany('''
            INSERT INTO terminal (title, description, filename, filetype, uploader, date_uploaded)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_terminal_data)
        print("✅ Sample terminal data inserted.")
    else:
        print("ℹ️ Terminal table already has data. Skipping sample insert.")

    # Users (admin) table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_password = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password))
        print("✅ Default admin created (username: admin, password: admin123)")
    else:
        print("⚠️ Admin user already exists.")

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

    conn.commit()
    conn.close()
    print("✅ Database setup complete.")

if __name__ == "__main__":
    setup_database()
