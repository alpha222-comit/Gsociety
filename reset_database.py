# reset_database.py

import os
from app import app, init_db

# --- THE SCRIPT'S ACTION ---

print("--- [DATABASE RESET PROTOCOL INITIATED] ---")

# Forcibly delete the old database if it exists
if os.path.exists(app.config['DATABASE']):
    os.remove(app.config['DATABASE'])
    print(f"[+] Old database '{app.config['DATABASE']}' has been destroyed.")

print("[*] Rebuilding database from the current app.py blueprint...")

# Run the initialization function directly
init_db()

print("--- [DATABASE RESET PROTOCOL COMPLETE] ---")