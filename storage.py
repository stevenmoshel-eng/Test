import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import config


@contextmanager
def _connect():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                text TEXT NOT NULL,
                summary TEXT,
                UNIQUE(channel, message_id)
            )
            """
        )


def insert_post(channel, message_id, date, text):
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO posts (channel, message_id, date, text)
            VALUES (?, ?, ?, ?)
            """,
            (channel, message_id, date, text),
        )


def get_unsummarized_posts():
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, text FROM posts WHERE summary IS NULL"
        ).fetchall()
        return [dict(row) for row in rows]


def set_summary(post_id, summary):
    with _connect() as conn:
        conn.execute("UPDATE posts SET summary = ? WHERE id = ?", (summary, post_id))


def get_recent_posts(hours=24):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT channel, date, text, summary
            FROM posts
            WHERE date >= ?
            ORDER BY date DESC
            """,
            (cutoff,),
        ).fetchall()
        return [dict(row) for row in rows]
