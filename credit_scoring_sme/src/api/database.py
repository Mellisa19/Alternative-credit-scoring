import sqlite3
import os
import json
from datetime import datetime

DATABASE_URL = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Assessments table for premium history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            risk_tier TEXT NOT NULL,
            decision_summary TEXT,
            inputs_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Simple migration for Phase IV fields
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN loan_purpose TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN business_age TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN repayment_confidence TEXT")
        
        cursor.execute("ALTER TABLE assessments ADD COLUMN loan_purpose TEXT")
        cursor.execute("ALTER TABLE assessments ADD COLUMN business_age TEXT")
        cursor.execute("ALTER TABLE assessments ADD COLUMN repayment_confidence TEXT")
    except sqlite3.OperationalError:
        # Columns probably already exist
        pass

    conn.commit()
    conn.close()

def create_user(email, hashed_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def update_user_profile(user_id, loan_purpose, business_age, repayment_confidence):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users 
            SET loan_purpose = ?, business_age = ?, repayment_confidence = ?
            WHERE id = ?
        """, (loan_purpose, business_age, repayment_confidence, user_id))
        conn.commit()
    finally:
        conn.close()

def save_assessment(user_id, score, risk_tier, summary, inputs, loan_purpose=None, business_age=None, repayment_confidence=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        inputs_json = json.dumps(inputs)
        cursor.execute("""
            INSERT INTO assessments (user_id, score, risk_tier, decision_summary, inputs_json, loan_purpose, business_age, repayment_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, score, risk_tier, summary, inputs_json, loan_purpose, business_age, repayment_confidence))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error saving assessment: {e}")
        return None
    finally:
        conn.close()

def get_latest_assessments(user_id, limit=2):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM assessments 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
