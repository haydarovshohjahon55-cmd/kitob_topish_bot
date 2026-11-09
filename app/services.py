"""Biznes mantiq qatlami (L3, L4). Telegram haqida hech narsa bilmaydi."""
from __future__ import annotations

import math

from app.events import BookAdded, BookDownloaded, EventBus, SearchPerformed
from app.models import ROLE_ADMIN, ROLE_USER, Book, Page, User
from app.repositories import BookRepository, UserRepository
from app.search import get_strategy
from app.utils import normalize

MIN_QUERY_LEN = 2


class BookNotFound(Exception):
    pass


class BookService:
    def __init__(self, repo: BookRepository, events: EventBus, page_size: int = 5):
        self.repo = repo          # Dependency Injection (L5)
        self.events = events
        self.page_size = page_size

    def add_from_channel(self, *, title, author, genre, file_id, file_name,
                         file_size, channel_id, message_id) -> Book | None:
        book = Book(
            title=title, author=author, genre=genre, file_id=file_id,
            file_name=file_name, file_size=file_size,
            channel_id=channel_id, message_id=message_id,
        )
        saved = self.repo.add(book)
        if saved:
            self.events.publish(BookAdded(saved))
        return saved

    def search(self, mode: str, query: str, page: int = 1, user_id: int | None = None) -> Page:
        strategy = get_strategy(mode)
        term = normalize(query)
        if strategy.columns and len(term) < MIN_QUERY_LEN:
            raise ValueError(f"So'rov kamida {MIN_QUERY_LEN} ta belgidan iborat bo'lsin.")
        total = self.repo.count(strategy.columns, term)
        pages = max(1, math.ceil(total / self.page_size))
        page = min(max(page, 1), pages)
        offset = (page - 1) * self.page_size
        items = self.repo.search(strategy.columns, term, self.page_size, offset)
        if page == 1 and user_id is not None and strategy.columns:
            self.events.publish(SearchPerformed(user_id, term, mode, total))
        return Page(items=items, total=total, page=page, pages=pages, offset=offset)

    def download(self, book_id: int, user_id: int) -> Book:
        book = self.repo.get(book_id)
        if book is None:
            raise BookNotFound(book_id)
        self.repo.increment_downloads(book_id)
        self.events.publish(BookDownloaded(book_id, user_id))
        return book

    def delete(self, book_id: int) -> bool:
        return self.repo.delete(book_id)

    def stats(self) -> tuple[int, int]:
        return self.repo.stats()


class UserService:
    def __init__(self, repo: UserRepository, admin_ids=frozenset()):
        self.repo = repo
        self.admin_ids = frozenset(admin_ids)

    def register(self, user_id: int, username: str | None, full_name: str) -> None:
        role = ROLE_ADMIN if user_id in self.admin_ids else ROLE_USER
        self.repo.upsert(User(user_id, username, full_name, role))
        if user_id in self.admin_ids:
            self.repo.set_role(user_id, ROLE_ADMIN)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids or self.repo.get_role(user_id) == ROLE_ADMIN

    def make_admin(self, user_id: int) -> bool:
        return self.repo.set_role(user_id, ROLE_ADMIN)

    def count(self) -> int:
        return self.repo.count()

    def admin_ids_all(self) -> set:
        return set(self.admin_ids) | set(self.repo.admin_ids())
