# database.py

import sqlite3
import time

from config import DB_NAME

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Users Table (7 data columns + user_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 100,
            death_ts REAL DEFAULT 0.0,
            protect_ts REAL DEFAULT 0.0,
            revive_count INTEGER DEFAULT 0,
            revive_date TEXT,
            total_kills INTEGER DEFAULT 0,
            daily_ts REAL DEFAULT 0.0
        )
    """)
    
    # 2. History Table (Name/Username History)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,  -- 'name' or 'username'
            value TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    
    # 3. Balance History Table (Balance Transaction History)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp REAL NOT NULL,
            type TEXT NOT NULL,       -- 'daily', 'kill_gain', 'rob_loss', etc.
            amount INTEGER NOT NULL,  -- The change amount
            details TEXT              
        )
    """)
    
    # 4. Groups Table (UPDATED to include claim data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY,
            added_by INTEGER,
            added_ts REAL,
            claimed_by_id INTEGER,
            claimed_ts REAL
        )
    """)
    
    conn.commit()
    conn.close()

# --- HELPER FUNCTIONS ---

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return data[1:] 
    
    set_user_data(user_id) 
    return (100, 0.0, 0.0, 0, None, 0, 0.0)

def set_user_data(user_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    for key, value in kwargs.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    if fields:
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
            values.append(user_id)
            cursor.execute(query, values)
        else:
            default_data = {
                'balance': 100, 'death_ts': 0.0, 'protect_ts': 0.0, 
                'revive_count': 0, 'revive_date': None, 'total_kills': 0, 
                'daily_ts': 0.0
            }
            default_data.update(kwargs)
            
            cols = ', '.join(['user_id'] + list(default_data.keys()))
            placeholders = ', '.join(['?'] * (len(default_data) + 1))
            insert_values = [user_id] + list(default_data.values())
            
            query = f"INSERT INTO users ({cols}) VALUES ({placeholders})"
            cursor.execute(query, insert_values)
            
    else:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def is_protected(protect_ts):
    return protect_ts > time.time()

def is_dead(death_ts):
    return death_ts > time.time()

def get_top_users(field, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT user_id, {field} FROM users ORDER BY {field} DESC LIMIT ?", (limit,))
    data = cursor.fetchall()
    conn.close()
    return data

def add_group_to_db(chat_id, added_by):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO groups (chat_id, added_by, added_ts) VALUES (?, ?, ?)",
        (chat_id, added_by, time.time())
    )
    conn.commit()
    conn.close()

# --- NAME/USERNAME HISTORY FUNCTIONS ---

def log_name_change(user_id, type, new_value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM user_history WHERE user_id = ? AND type = ? ORDER BY timestamp DESC LIMIT 1", (user_id, type))
    last_value = cursor.fetchone()
    if last_value is None or last_value[0] != new_value:
        cursor.execute("INSERT INTO user_history (user_id, type, value, timestamp) VALUES (?, ?, ?, ?)", (user_id, type, new_value, time.time()))
        conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT type, value, timestamp FROM user_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

# --- BALANCE HISTORY FUNCTIONS ---

def log_balance_change(user_id, type, amount, details=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO balance_history (user_id, timestamp, type, amount, details) VALUES (?, ?, ?, ?, ?)", (user_id, time.time(), type, amount, details))
    conn.commit()
    conn.close()

def get_balance_history(user_id, limit=15):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, type, amount, details FROM balance_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    return history
    
# --- GROUP CLAIM FUNCTIONS (NEW) ---

def get_group_claim_data(chat_id):
    """Fetches the user ID and timestamp of the group claim."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT claimed_by_id, claimed_ts FROM groups WHERE chat_id = ?", (chat_id,))
        data = cursor.fetchone()
    except sqlite3.OperationalError:
        conn.close()
        return None, None 

    conn.close()
    if data and data[0] is not None: 
        return data[0], data[1]
    return None, None 

def set_group_claim_data(chat_id, user_id, timestamp):
    """Sets the user ID and timestamp for the group claim."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("INSERT OR IGNORE INTO groups (chat_id, added_by, added_ts) VALUES (?, ?, ?)", 
                   (chat_id, user_id, time.time()))
    
    cursor.execute("UPDATE groups SET claimed_by_id = ?, claimed_ts = ? WHERE chat_id = ?", 
                   (user_id, timestamp, chat_id))
    conn.commit()
    conn.close()