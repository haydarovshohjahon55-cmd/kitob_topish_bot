"""Hodisalarga asoslangan modul: Producer -> EventBus -> Consumer (L9)."""
import logging
from collections import defaultdict
from dataclasses import dataclass

from app.models import Book

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BookAdded:
    book: Book


@dataclass(frozen=True)
class BookDownloaded:
    book_id: int
    user_id: int


@dataclass(frozen=True)
class SearchPerformed:
    user_id: int
    query: str
    mode: str
    found: int


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_type, handler):
        self._subscribers[event_type].append(handler)

    def publish(self, event):
        # Bitta consumer xatosi boshqalariga va asosiy jarayonga ta'sir qilmaydi.
        for handler in self._subscribers[type(event)]:
            try:
                handler(event)
            except Exception:
                logger.exception("Event handler xatosi: %s", type(event).__name__)
