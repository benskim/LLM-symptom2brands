import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "audit.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            brand_website TEXT NOT NULL,
            status TEXT DEFAULT 'complete',
            report_json TEXT,
            markdown_report TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_audit(brand_name: str, brand_website: str, report_json: dict, markdown: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO audits (brand_name, brand_website, status, report_json, markdown_report, created_at) "
        "VALUES (?, ?, 'complete', ?, ?, ?)",
        (brand_name, brand_website, json.dumps(report_json), markdown, now)
    )
    audit_id = c.lastrowid
    conn.commit()
    conn.close()
    return audit_id


def list_audits() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, brand_name, brand_website, status, created_at FROM audits ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
