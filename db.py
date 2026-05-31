import sqlite3
from contextlib import contextmanager

DB = "schedules.db"


def conn():
    return sqlite3.connect(DB)


@contextmanager
def get_db():
    c = conn()
    try:
        yield c
    finally:
        c.close()


def init():
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            slots TEXT NOT NULL,
            confirmed_slot INTEGER,
            created_by TEXT NOT NULL
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            schedule_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            available_slots TEXT NOT NULL,
            PRIMARY KEY (schedule_id, user_id),
            FOREIGN KEY (schedule_id) REFERENCES schedules(id)
        )
        """)
        try:
            db.execute("ALTER TABLE schedules ADD COLUMN book TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        db.commit()
