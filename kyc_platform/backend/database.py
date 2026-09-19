import sqlite3
import json
import threading
from datetime import datetime
from typing import Optional, List, Dict

from .config import DB_PATH
from .models import KYCState

_lock = threading.Lock()


# ─── Connection factory ───────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


# ─── Schema bootstrap ─────────────────────────────────────────────────────────

def init_db() -> None:
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS kyc_cases (
                customer_id TEXT PRIMARY KEY,
                state_json  TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'processing',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT    NOT NULL,
                event_type  TEXT    NOT NULL,
                event_data  TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL
            )
        """)
        c.commit()
    print(f"✅  Database ready: {DB_PATH}")


# ─── KYC state CRUD ───────────────────────────────────────────────────────────

def save_state(state: KYCState) -> None:
    now    = datetime.utcnow().isoformat()
    status = state.get("final_decision") or "processing"
    with _lock:
        with _conn() as c:
            c.execute(
                """
                INSERT INTO kyc_cases (customer_id, state_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    state_json = excluded.state_json,
                    status     = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (state["customer_id"], json.dumps(state), status, now, now),
            )
            c.commit()


def load_state(customer_id: str) -> Optional[KYCState]:
    with _conn() as c:
        row = c.execute(
            "SELECT state_json FROM kyc_cases WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    return json.loads(row["state_json"]) if row else None


def list_cases(status_filter: Optional[str] = None) -> List[Dict]:
    with _conn() as c:
        if status_filter:
            rows = c.execute(
                "SELECT state_json FROM kyc_cases WHERE status = ? ORDER BY updated_at DESC",
                (status_filter,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT state_json FROM kyc_cases ORDER BY updated_at DESC"
            ).fetchall()
    return [json.loads(r["state_json"]) for r in rows]


# ─── Audit log ────────────────────────────────────────────────────────────────

def log_audit_event(customer_id: str, event_type: str, event_data: Dict) -> None:
    with _lock:
        with _conn() as c:
            c.execute(
                "INSERT INTO audit_log (customer_id, event_type, event_data, timestamp) "
                "VALUES (?, ?, ?, ?)",
                (customer_id, event_type, json.dumps(event_data), datetime.utcnow().isoformat()),
            )
            c.commit()

def clear_audit_log() -> None:
    with _lock:
        with _conn() as c:
            c.execute("DELETE FROM audit_log")
            c.commit()


def get_audit_log(customer_id: Optional[str] = None) -> List[Dict]:
    with _conn() as c:
        if customer_id:
            rows = c.execute(
                "SELECT * FROM audit_log WHERE customer_id = ? ORDER BY timestamp",
                (customer_id,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 500"
            ).fetchall()
    return [
        {
            "id":          r["id"],
            "customer_id": r["customer_id"],
            "event_type":  r["event_type"],
            "event_data":  json.loads(r["event_data"]),
            "timestamp":   r["timestamp"],
        }
        for r in rows
    ]
