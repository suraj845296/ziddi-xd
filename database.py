import sqlite3
import hashlib
import uuid
from pathlib import Path

DB_FILE = "users.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_config (
            user_id TEXT PRIMARY KEY,
            chat_id TEXT DEFAULT '',
            name_prefix TEXT DEFAULT '',
            delay INTEGER DEFAULT 30,
            cookies TEXT DEFAULT '',
            messages TEXT DEFAULT 'Hello!',
            automation_running BOOLEAN DEFAULT 0,
            admin_e2ee_thread_id TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already exists!"
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute(
            'INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)',
            (user_id, username, password_hash)
        )
        
        # Create default config
        cursor.execute(
            'INSERT INTO user_config (user_id) VALUES (?)',
            (user_id,)
        )
        
        conn.commit()
        conn.close()
        return True, "User created successfully!"
    except Exception as e:
        return False, str(e)

def verify_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        'SELECT id FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return user['id']
    return None

def get_username(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user['username'] if user else 'Unknown'

def get_user_config(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_config WHERE user_id = ?', (user_id,))
    config = cursor.fetchone()
    conn.close()
    
    if config:
        return {
            'chat_id': config['chat_id'] or '',
            'name_prefix': config['name_prefix'] or '',
            'delay': config['delay'] or 30,
            'cookies': config['cookies'] or '',
            'messages': config['messages'] or 'Hello!'
        }
    return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_config 
        SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?
        WHERE user_id = ?
    ''', (chat_id, name_prefix, delay, cookies, messages, user_id))
    conn.commit()
    conn.close()

def set_automation_running(user_id, running):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE user_config SET automation_running = ? WHERE user_id = ?',
        (1 if running else 0, user_id)
    )
    conn.commit()
    conn.close()

def get_automation_running(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT automation_running FROM user_config WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return bool(result['automation_running']) if result else False

def set_admin_e2ee_thread_id(user_id, thread_id, cookies, chat_type):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_config 
        SET admin_e2ee_thread_id = ?, cookies = ?
        WHERE user_id = ?
    ''', (thread_id, cookies, user_id))
    conn.commit()
    conn.close()

def get_admin_e2ee_thread_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT admin_e2ee_thread_id FROM user_config WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['admin_e2ee_thread_id'] if result and result['admin_e2ee_thread_id'] else None

# Initialize database when module is imported
init_db()
