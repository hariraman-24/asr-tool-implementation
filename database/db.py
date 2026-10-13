"""
Database layer for MeetBrief: Live Meeting Platform with ASR MoM Generation.
Stores Minutes of Meeting (MoM) records cleanly in SQLite.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "meetbrief.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        duration TEXT DEFAULT '00:00',
        mom_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_meeting_mom(title, mom_text, duration="00:00", date_str=None, time_str=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    if not date_str:
        date_str = now.strftime("%Y-%m-%d")
    if not time_str:
        time_str = now.strftime("%I:%M %p")

    cursor.execute("""
        INSERT INTO meetings (title, date, time, duration, mom_text)
        VALUES (?, ?, ?, ?, ?)
    """, (title, date_str, time_str, duration, mom_text))
    meeting_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return meeting_id

def get_all_meetings(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_meeting_by_id(meeting_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_meeting(meeting_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
