"""Repository interfeyslari va SQLite realizatsiyalari (L3, L4, L8)."""
from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod

from app.database import Database
from app.models import ROLE_ADMIN, Book, User
from app.utils import escape_like, normalize

BOOK_COLS = (
    "id, title, author, genre, file_id, file_name, file_size, "
    "channel_id, message_id, downloads, created_at"
)
_ALLOWED_COLUMNS = {"title_norm", "author_norm", "genre_norm"}
_ESC = " ESCAPE '\\'"


def _row_to_book(row: sqlite3.Row) -> Book:
    return Book(**{k: row[k] for k in row.keys()})


def _build_where(columns: tuple, term: str) -> tuple[str, list]:
    """Har bir so'z (token) kamida bitta ustunda uchrashi kerak (AND/OR)."""
    if not columns or not term:
        return "", []
    if not set(columns) <= _ALLOWED_COLUMNS:
        raise ValueError("Ruxsat etilmagan ustun")
    clauses, params = [], []
    for token in term.split():
        like = f"%{escape_like(token)}%"
        group = " OR ".join(f"{c} LIKE ?{_ESC}" for c in columns)
        clauses.append(f"({group})")
        params.extend([like] * len(columns))
    return " WHERE " + " AND ".join(clauses), params


class BookRepository(ABC):
    @abstractmethod
    def add(self, book: Book) -> Book | None: ...

    @abstractmethod
    def get(self, book_id: int) -> Book | None: ...

    @abstractmethod
    def search(self, columns: tuple, term: str, limit: int, offset: int) -> list: ...

    @abstractmethod
    def count(self, columns: tuple, term: str) -> int: ...

    @abstractmethod
    def delete(self, book_id: int) -> bool: ...

    @abstractmethod
    def increment_downloads(self, book_id: int) -> None: ...

    @abstractmethod
    def stats(self) -> tuple[int, int]: ...


class SqliteBookRepository(BookRepository):
    def __init__(self, db: Database):
        self.db = db

    def add(self, book: Book) -> Book | None:
        try:
            with self.db.connection() as conn:
                cur = conn.execute(
                    """INSERT INTO books (title, author, genre, title_norm, author_norm,
                       genre_norm, file_id, file_name, file_size, channel_id, message_id)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        book.title, book.author, book.genre,
                        normalize(book.title), normalize(book.author), normalize(book.genre),
                        book.file_id, book.file_name, book.file_size,
                        book.channel_id, book.message_id,
                    ),
                )
                new_id = cur.lastrowid
        except sqlite3.IntegrityError:
            return None  # shu post allaqachon qo'shilgan
        return self.get(new_id)

    def get(self, book_id: int) -> Book | None:
        with self.db.connection() as conn:
            row = conn.execute(
                f"SELECT {BOOK_COLS} FROM books WHERE id = ?", (book_id,)
            ).fetchone()
        return _row_to_book(row) if row else None

    def search(self, columns, term, limit, offset):
        where, params = _build_where(columns, term)
        sql = f"SELECT {BOOK_COLS} FROM books{where} ORDER BY id DESC LIMIT ? OFFSET ?"
        with self.db.connection() as conn:
            rows = conn.execute(sql, [*params, limit, offset]).fetchall()
        return [_row_to_book(r) for r in rows]

    def count(self, columns, term):
        where, params = _build_where(columns, term)
        with self.db.connection() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM books{where}", params).fetchone()[0]

    def delete(self, book_id: int) -> bool:
        with self.db.connection() as conn:
            return conn.execute("DELETE FROM books WHERE id = ?", (book_id,)).rowcount > 0

    def increment_downloads(self, book_id: int) -> None:
        with self.db.connection() as conn:
            conn.execute("UPDATE books SET downloads = downloads + 1 WHERE id = ?", (book_id,))

    def stats(self):
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(downloads), 0) FROM books"
            ).fetchone()
        return row[0], row[1]


class UserRepository(ABC):
    @abstractmethod
    def upsert(self, user: User) -> None: ...

    @abstractmethod
    def get_role(self, user_id: int) -> str | None: ...

    @abstractmethod
    def set_role(self, user_id: int, role: str) -> bool: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def admin_ids(self) -> list: ...


class SqliteUserRepository(UserRepository):
    def __init__(self, db: Database):
        self.db = db

    def upsert(self, user: User) -> None:
        with self.db.connection() as conn:
            conn.execute(
                """INSERT INTO users (user_id, username, full_name, role) VALUES (?,?,?,?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   username = excluded.username, full_name = excluded.full_name""",
                (user.user_id, user.username, user.full_name, user.role),
            )

    def get_role(self, user_id):
        with self.db.connection() as conn:
            row = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row["role"] if row else None

    def set_role(self, user_id, role):
        with self.db.connection() as conn:
            return conn.execute(
                "UPDATE users SET role = ? WHERE user_id = ?", (role, user_id)
            ).rowcount > 0

    def count(self):
        with self.db.connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def admin_ids(self):
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT user_id FROM users WHERE role = ?", (ROLE_ADMIN,)
            ).fetchall()
        return [r["user_id"] for r in rows]


class SqliteSearchLogRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, user_id: int, query: str, mode: str, found: int) -> None:
        with self.db.connection() as conn:
            conn.execute(
                "INSERT INTO search_log (user_id, query, mode, results_count) VALUES (?,?,?,?)",
                (user_id, normalize(query), mode, found),
            )

    def top_queries(self, limit: int = 5) -> list:
        with self.db.connection() as conn:
            rows = conn.execute(
                """SELECT query, COUNT(*) AS c FROM search_log
                   GROUP BY query ORDER BY c DESC, query LIMIT ?""",
                (limit,),
            ).fetchall()
        return [(r["query"], r["c"]) for r in rows]
