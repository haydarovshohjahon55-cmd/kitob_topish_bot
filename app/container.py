"""Barcha bog'liqliklarni bir joyda yig'ish (Dependency Injection, L3/L5)."""
import logging
from dataclasses import dataclass, field

from app.database import Database
from app.events import BookAdded, BookDownloaded, EventBus, SearchPerformed
from app.metrics import Metrics
from app.repositories import (
    SqliteBookRepository,
    SqliteSearchLogRepository,
    SqliteUserRepository,
)
from app.services import BookService, UserService
from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    settings: Settings
    db: Database
    events: EventBus
    metrics: Metrics
    books: BookService
    users: UserService
    searches: SqliteSearchLogRepository
    state: dict = field(default_factory=dict)  # user_id -> {"mode":..., "query":...}


def build_context(settings: Settings) -> AppContext:
    db = Database(settings.db_path)
    db.migrate()
    events, metrics = EventBus(), Metrics()
    ctx = AppContext(
        settings=settings, db=db, events=events, metrics=metrics,
        books=BookService(SqliteBookRepository(db), events, settings.page_size),
        users=UserService(SqliteUserRepository(db), settings.admin_ids),
        searches=SqliteSearchLogRepository(db),
    )

    def on_book_added(e: BookAdded):
        metrics.incr("books.added")
        logger.info("Yangi kitob: #%s %s", e.book.id, e.book.title)

    def on_downloaded(e: BookDownloaded):
        metrics.incr("books.downloaded")

    def on_search(e: SearchPerformed):
        metrics.incr("search.count")
        if e.found == 0:
            metrics.incr("search.empty")
        ctx.searches.add(e.user_id, e.query, e.mode, e.found)

    events.subscribe(BookAdded, on_book_added)
    events.subscribe(BookDownloaded, on_downloaded)
    events.subscribe(SearchPerformed, on_search)
    return ctx
