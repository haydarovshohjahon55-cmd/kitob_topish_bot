"""SQLite ulanishi, migratsiyalar va tranzaksiyalar (L8)."""
import logging
import os
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Har bir element = bitta migratsiya. PRAGMA user_version joriy versiyani saqlaydi.
MIGRATIONS = [
    # 1: asosiy jadvallar
    """
    CREATE TABLE users (
        user_id    INTEGER PRIMARY KEY,
        username   TEXT,
        full_name  TEXT NOT NULL DEFAULT '',
        role       TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE books (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        author      TEXT NOT NULL,
        genre       TEXT NOT NULL,
        title_norm  TEXT NOT NULL,
        author_norm TEXT NOT NULL,
        genre_norm  TEXT NOT NULL,
        file_id     TEXT NOT NULL,
        file_name   TEXT NOT NULL DEFAULT '',
        file_size   INTEGER NOT NULL DEFAULT 0,
        channel_id  INTEGER NOT NULL,
        message_id  INTEGER NOT NULL,
        downloads   INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (channel_id, message_id)
    );
    CREATE INDEX idx_books_title  ON books(title_norm);
    CREATE INDEX idx_books_author ON books(author_norm);
    """,
    # 2: qidiruv tarixi (statistika uchun)
    """
    CREATE TABLE search_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL REFERENCES users(user_id),
        query         TEXT NOT NULL,
        mode          TEXT NOT NULL,
        results_count INTEGER NOT NULL,
        created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
]


class Database:
    def __init__(self, path: str):
        self.path = path
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

    @contextmanager
    def connection(self):
        """Har bir chaqiruvga alohida ulanish (telebot ko'p oqimli).
        Xatolik bo'lsa ROLLBACK, aks holda COMMIT bajariladi."""
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def migrate(self) -> int:
        with self.connection() as conn:
            current = conn.execute("PRAGMA user_version").fetchone()[0]
            for version, script in enumerate(MIGRATIONS, start=1):
                if version > current:
                    logger.info("Migratsiya #%s qo'llanmoqda", version)
                    conn.executescript(script)
                    conn.execute(f"PRAGMA user_version = {version}")
            return len(MIGRATIONS)
