"""Domen obyektlari (L4)."""
from __future__ import annotations

from dataclasses import dataclass

ROLE_USER = "user"
ROLE_ADMIN = "admin"


@dataclass
class Book:
    title: str
    author: str
    genre: str
    file_id: str
    file_name: str = ""
    file_size: int = 0
    channel_id: int = 0
    message_id: int = 0
    downloads: int = 0
    id: int | None = None
    created_at: str = ""


@dataclass
class User:
    user_id: int
    username: str | None
    full_name: str
    role: str = ROLE_USER


@dataclass
class Page:
    items: list
    total: int
    page: int
    pages: int
    offset: int = 0
