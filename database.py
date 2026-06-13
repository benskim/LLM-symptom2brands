import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "data/audits.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            brand_website TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            report_json TEXT,
            markdown_report TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_audit(brand_name: str, brand_website: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO audits (brand_name, brand_website, status, created_at, updated_at) VALUES (?, ?, 'running', ?, ?)",
        (brand_name, brand_website, now, now)
    )
    audit_id = c.lastrowid
    conn.commit()
    conn.close()
    return audit_id


def update_audit(audit_id: int, status: str, report_json: dict = None, markdown_report: str = ""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute(
        "UPDATE audits SET status=?, report_json=?, markdown_report=?, updated_at=? WHERE id=?",
        (
            status,
            json.dumps(report_json) if report_json else None,
            markdown_report,
            now,
            audit_id
        )
    )
    conn.commit()
    conn.close()


def get_audit(audit_id: int) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM audits WHERE id=?", (audit_id,))
    row = c.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("report_json"):
            d["report_json"] = json.loads(d["report_json"])
        return d
    return None


def list_audits() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, brand_name, brand_website, status, created_at, updated_at FROM audits ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
