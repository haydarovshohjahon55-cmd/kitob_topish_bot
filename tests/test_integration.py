"""Integratsion testlar: Service + haqiqiy SQLite bazasi (L11)."""
import pytest

from app.container import build_context
from config import Settings


@pytest.fixture
def ctx(tmp_path):
    settings = Settings(token="t", channel_id=-100, admin_ids=frozenset({1}),
                        db_path=str(tmp_path / "test.db"), page_size=3)
    c = build_context(settings)
    c.users.register(1, "admin", "Admin")
    c.users.register(2, "user", "User")
    return c


def add(ctx, n, title, author="Muallif", genre="Roman"):
    return ctx.books.add_from_channel(
        title=title, author=author, genre=genre, file_id=f"file{n}",
        file_name=f"{n}.pdf", file_size=10, channel_id=-100, message_id=n)


def test_migrations_applied_once(ctx):
    assert ctx.db.migrate() == 2
    with ctx.db.connection() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2


def test_search_by_title_author_and_apostrophe(ctx):
    add(ctx, 1, "O‘tkan kunlar", "Abdulla Qodiriy")
    add(ctx, 2, "Mehrobdan chayon", "Abdulla Qodiriy")
    add(ctx, 3, "Sariq devni minib", "Xudoyberdi To‘xtaboyev", "Bolalar")
    assert ctx.books.search("title", "o'tkan").total == 1
    assert ctx.books.search("author", "QODIRIY").total == 2
    assert ctx.books.search("all", "bolalar").total == 1
    assert ctx.books.search("all", "abdulla chayon").total == 1  # ikki so'z, AND
    assert ctx.books.search("all", "yo'q kitob").total == 0


def test_like_wildcards_are_escaped(ctx):
    add(ctx, 1, "100% xavfsiz")
    add(ctx, 2, "Oddiy kitob")
    assert ctx.books.search("title", "%%").total == 0


def test_pagination(ctx):
    for i in range(1, 8):
        add(ctx, i, f"Kitob {i}")
    p1 = ctx.books.search("latest", "")
    assert (p1.total, p1.pages, len(p1.items)) == (7, 3, 3)
    p3 = ctx.books.search("latest", "", page=3)
    assert len(p3.items) == 1
    assert ctx.books.search("latest", "", page=99).page == 3  # chegaradan oshmaydi


def test_duplicate_post_rejected(ctx):
    assert add(ctx, 1, "A kitob") is not None
    assert add(ctx, 1, "A kitob") is None
    assert ctx.books.stats()[0] == 1


def test_download_counter_and_search_log(ctx):
    book = add(ctx, 1, "Kitob nomi")
    ctx.books.download(book.id, 2)
    ctx.books.download(book.id, 2)
    assert ctx.books.stats() == (1, 2)
    ctx.books.search("title", "kitob", user_id=2)
    assert ctx.searches.top_queries() == [("kitob", 1)]
    assert ctx.metrics.counters["books.downloaded"] == 2


def test_delete_book(ctx):
    book = add(ctx, 1, "Kitob")
    assert ctx.books.delete(book.id) is True
    assert ctx.books.delete(book.id) is False


def test_roles(ctx):
    assert ctx.users.is_admin(1)
    assert not ctx.users.is_admin(2)
    ctx.users.make_admin(2)
    assert ctx.users.is_admin(2)
