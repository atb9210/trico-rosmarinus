import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional

DB_PATH = os.getenv("DB_PATH", "/app/data/trico.db")


def get_db():
    """Get database connection with row factory."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            aff_sub1 TEXT,
            aff_sub2 TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            http_status INTEGER,
            worldfilia_response TEXT,
            error TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_lead(
    name: str,
    phone: str,
    address: str,
    aff_sub1: str = None,
    aff_sub2: str = None,
    status: str = "pending",
    http_status: int = None,
    worldfilia_response: str = None,
    error: str = None,
) -> int:
    """Save a lead to the database. Returns the lead ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO leads (name, phone, address, aff_sub1, aff_sub2, status, http_status, worldfilia_response, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, phone, address, aff_sub1, aff_sub2, status, http_status, worldfilia_response, error),
    )
    conn.commit()
    lead_id = cursor.lastrowid
    conn.close()
    return lead_id


def get_leads(page: int = 1, limit: int = 50, date_filter: str = None) -> Dict:
    """Get paginated leads list."""
    conn = get_db()
    cursor = conn.cursor()

    offset = (page - 1) * limit

    if date_filter:
        cursor.execute(
            "SELECT COUNT(*) FROM leads WHERE DATE(created_at) = ?", (date_filter,)
        )
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM leads WHERE DATE(created_at) = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (date_filter, limit, offset),
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM leads")
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )

    rows = cursor.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()

    return {
        "leads": leads,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1,
    }


def get_lead_stats() -> Dict:
    """Get lead statistics."""
    conn = get_db()
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE DATE(created_at) = ?", (today,))
    today_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'success'")
    success = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'failed'")
    failed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'success' AND DATE(created_at) = ?", (today,))
    today_success = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'failed' AND DATE(created_at) = ?", (today,))
    today_failed = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "today": today_count,
        "success": success,
        "failed": failed,
        "today_success": today_success,
        "today_failed": today_failed,
        "success_rate": round((success / total * 100), 1) if total > 0 else 0,
        "date": today,
    }
