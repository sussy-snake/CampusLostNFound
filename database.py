"""
database.py
───────────
DatabaseManager — the single gateway to the SQLite database.
All SQL lives here; no raw SQL elsewhere in the project.
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from config import DB_PATH


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Return (hashed_password, salt) using SHA-256 + random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return hashed, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Return True if *password* matches *stored_hash*."""
    computed, _ = _hash_password(password, salt)
    return computed == stored_hash


# ── DatabaseManager ─────────────────────────────────────────────────────────────

class DatabaseManager:
    """
    Encapsulates every database interaction for Campus Lost-and-Found.
    Usage:
        db = DatabaseManager()          # connects and migrates once
        user = db.get_user("alice")
    """

    def __init__(self, path: str = DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row      # dict-like row access
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    # ── Schema Migration ───────────────────────────────────────────────────────

    def _migrate(self):
        """Create all tables if they do not exist yet."""
        cur = self.conn.cursor()

        # Users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT UNIQUE NOT NULL,
                password   TEXT NOT NULL,
                salt       TEXT NOT NULL,
                sec_q      TEXT,          -- security question text
                sec_a      TEXT,          -- hashed security answer
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Items  (lost / found)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                item_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                type         TEXT NOT NULL CHECK(type IN ('lost','found')),
                category     TEXT NOT NULL,
                color        TEXT NOT NULL,
                brand        TEXT,
                date_lost    TEXT,
                location     TEXT,
                description  TEXT,
                image_path   TEXT,
                user_id      INTEGER NOT NULL REFERENCES users(user_id),
                status       TEXT NOT NULL DEFAULT 'pending'
                             CHECK(status IN ('pending','matched','returned','closed')),
                created_at   TEXT DEFAULT (datetime('now'))
            )
        """)

        # Matches
        cur.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                lost_item_id  INTEGER NOT NULL REFERENCES items(item_id),
                found_item_id INTEGER NOT NULL REFERENCES items(item_id),
                score         REAL,          -- similarity score 0–1
                status        TEXT NOT NULL DEFAULT 'active'
                              CHECK(status IN ('active','resolved','dismissed')),
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)

        # Notifications
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notif_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(user_id),
                match_id    INTEGER REFERENCES matches(match_id),
                message     TEXT NOT NULL,
                is_read     INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # Chat messages
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                msg_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id    INTEGER NOT NULL REFERENCES matches(match_id),
                sender_id   INTEGER NOT NULL REFERENCES users(user_id),
                receiver_id INTEGER NOT NULL REFERENCES users(user_id),
                message_text TEXT NOT NULL,
                timestamp   TEXT DEFAULT (datetime('now'))
            )
        """)

        self.conn.commit()

    # ── User Operations ────────────────────────────────────────────────────────

    def register_user(self, username: str, password: str,
                      sec_q: str = "", sec_a: str = "") -> dict:
        """
        Register a new user.  Returns {'ok': True} or {'ok': False, 'err': msg}.
        """
        try:
            hashed, salt = _hash_password(password)
            # hash the security answer too
            hashed_ans, _ = _hash_password(sec_a.strip().lower(), salt) if sec_a else ("", "")
            self.conn.execute(
                "INSERT INTO users (username, password, salt, sec_q, sec_a) "
                "VALUES (?, ?, ?, ?, ?)",
                (username.strip(), hashed, salt, sec_q, hashed_ans),
            )
            self.conn.commit()
            return {"ok": True}
        except sqlite3.IntegrityError:
            return {"ok": False, "err": "Username already taken."}
        except Exception as e:
            return {"ok": False, "err": str(e)}

    def login_user(self, username: str, password: str) -> dict:
        """
        Authenticate.  Returns {'ok': True, 'user': Row} or {'ok': False, 'err': msg}.
        """
        row = self.conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        ).fetchone()
        if row is None:
            return {"ok": False, "err": "No account with that username."}
        if not _verify_password(password, row["password"], row["salt"]):
            return {"ok": False, "err": "Incorrect password."}
        return {"ok": True, "user": dict(row)}

    def get_user_by_id(self, user_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def verify_security_answer(self, username: str, answer: str) -> bool:
        row = self.conn.execute(
            "SELECT salt, sec_a FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row or not row["sec_a"]:
            return False
        hashed_ans, _ = _hash_password(answer.strip().lower(), row["salt"])
        return hashed_ans == row["sec_a"]

    def reset_password(self, username: str, new_password: str) -> bool:
        row = self.conn.execute(
            "SELECT salt FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return False
        hashed, _ = _hash_password(new_password, row["salt"])
        self.conn.execute(
            "UPDATE users SET password = ? WHERE username = ?", (hashed, username)
        )
        self.conn.commit()
        return True

    def get_security_question(self, username: str) -> str | None:
        row = self.conn.execute(
            "SELECT sec_q FROM users WHERE username = ?", (username,)
        ).fetchone()
        return row["sec_q"] if row else None

    # ── Item Operations ────────────────────────────────────────────────────────

    def add_item(self, item_type: str, category: str, color: str, brand: str,
                 date_lost: str, location: str, description: str,
                 image_path: str, user_id: int) -> int:
        """Insert a lost/found item and return its item_id."""
        cur = self.conn.execute(
            """INSERT INTO items
               (type, category, color, brand, date_lost, location,
                description, image_path, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_type, category.strip(), color.strip(), brand.strip(),
             date_lost, location.strip(), description.strip(),
             image_path, user_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_items_by_user(self, user_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_lost_items(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM items WHERE type='lost' AND status='pending'"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_item_by_id(self, item_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM items WHERE item_id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_item_status(self, item_id: int, status: str):
        self.conn.execute(
            "UPDATE items SET status = ? WHERE item_id = ?", (status, item_id)
        )
        self.conn.commit()

    # ── Match Operations ───────────────────────────────────────────────────────

    def create_match(self, lost_id: int, found_id: int, score: float) -> int:
        cur = self.conn.execute(
            "INSERT INTO matches (lost_item_id, found_item_id, score) VALUES (?,?,?)",
            (lost_id, found_id, score),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_match_by_id(self, match_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM matches WHERE match_id = ?", (match_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_matches_for_user(self, user_id: int) -> list[dict]:
        """Return all matches where user owns the lost item."""
        rows = self.conn.execute(
            """SELECT m.*, i_lost.category, i_lost.color, i_lost.brand,
                      i_found.user_id AS finder_id
               FROM matches m
               JOIN items i_lost  ON m.lost_item_id  = i_lost.item_id
               JOIN items i_found ON m.found_item_id = i_found.item_id
               WHERE i_lost.user_id = ?
               ORDER BY m.created_at DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_match_for_item(self, item_id: int) -> dict | None:
        """
        Return the most recent active (or any) match where this item
        appears as either the lost or the found side.
        Used to let finders open chat directly from My Reports.
        """
        row = self.conn.execute(
            """SELECT * FROM matches
               WHERE (lost_item_id = ? OR found_item_id = ?)
               ORDER BY CASE status WHEN 'active' THEN 0 ELSE 1 END,
                        created_at DESC
               LIMIT 1""",
            (item_id, item_id),
        ).fetchone()
        return dict(row) if row else None

    def resolve_match(self, match_id: int):
        self.conn.execute(
            "UPDATE matches SET status='resolved' WHERE match_id=?", (match_id,)
        )
        self.conn.commit()

    # ── Notification Operations ────────────────────────────────────────────────

    def add_notification(self, user_id: int, match_id: int, message: str):
        self.conn.execute(
            "INSERT INTO notifications (user_id, match_id, message) VALUES (?,?,?)",
            (user_id, match_id, message),
        )
        self.conn.commit()

    def get_notifications(self, user_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def mark_notifications_read(self, user_id: int):
        self.conn.execute(
            "UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,)
        )
        self.conn.commit()

    def unread_count(self, user_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM notifications WHERE user_id=? AND is_read=0",
            (user_id,),
        ).fetchone()
        return row["n"] if row else 0

    # ── Chat / Message Operations ──────────────────────────────────────────────

    def send_message(self, match_id: int, sender_id: int,
                     receiver_id: int, text: str) -> int:
        cur = self.conn.execute(
            """INSERT INTO messages (match_id, sender_id, receiver_id, message_text)
               VALUES (?,?,?,?)""",
            (match_id, sender_id, receiver_id, text),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_messages(self, match_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM messages WHERE match_id=? ORDER BY timestamp ASC",
            (match_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def close(self):
        self.conn.close()
