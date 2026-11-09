"""Unit testlar: repository mock bilan almashtirilgan (L11, Arrange-Act-Assert)."""
from unittest.mock import MagicMock

import pytest

from app.events import BookAdded, EventBus
from app.models import Book
from app.repositories import BookRepository
from app.services import BookNotFound, BookService


def make_service():
    repo = MagicMock(spec=BookRepository)
    events = EventBus()
    return BookService(repo, events, page_size=5), repo, events


def test_short_query_rejected():
    service, repo, _ = make_service()
    with pytest.raises(ValueError):
        service.search("all", "a")
    repo.count.assert_not_called()


def test_add_publishes_event():
    service, repo, events = make_service()
    repo.add.return_value = Book(title="T", author="A", genre="G", file_id="f", id=1)
    got = []
    events.subscribe(BookAdded, got.append)
    service.add_from_channel(title="T", author="A", genre="G", file_id="f",
                             file_name="", file_size=0, channel_id=-1, message_id=1)
    assert len(got) == 1 and got[0].book.id == 1


def test_duplicate_add_publishes_nothing():
    service, repo, events = make_service()
    repo.add.return_value = None
    got = []
    events.subscribe(BookAdded, got.append)
    assert service.add_from_channel(title="T", author="A", genre="G", file_id="f",
                                    file_name="", file_size=0, channel_id=-1, message_id=1) is None
    assert got == []


def test_download_unknown_book():
    service, repo, _ = make_service()
    repo.get.return_value = None
    with pytest.raises(BookNotFound):
        service.download(99, 1)
    repo.increment_downloads.assert_not_called()


def test_failing_subscriber_does_not_break_flow():
    service, repo, events = make_service()
    repo.add.return_value = Book(title="T", author="A", genre="G", file_id="f", id=1)
    events.subscribe(BookAdded, lambda e: 1 / 0)
    assert service.add_from_channel(title="T", author="A", genre="G", file_id="f",
                                    file_name="", file_size=0, channel_id=-1, message_id=1)
