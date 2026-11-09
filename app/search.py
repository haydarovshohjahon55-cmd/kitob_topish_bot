"""Qidiruv strategiyalari: Strategy + Factory patternlari (L5)."""
from abc import ABC


class SearchStrategy(ABC):
    name: str = ""
    columns: tuple = ()


class TitleSearch(SearchStrategy):
    name = "title"
    columns = ("title_norm",)


class AuthorSearch(SearchStrategy):
    name = "author"
    columns = ("author_norm",)


class AnySearch(SearchStrategy):
    name = "all"
    columns = ("title_norm", "author_norm", "genre_norm")


class LatestSearch(SearchStrategy):
    """Filtrsiz — oxirgi qo'shilgan kitoblar."""
    name = "latest"
    columns = ()


_STRATEGIES = {s.name: s for s in (TitleSearch, AuthorSearch, AnySearch, LatestSearch)}


def get_strategy(mode: str) -> SearchStrategy:
    """Factory: rejim nomiga qarab strategiya obyektini qaytaradi."""
    try:
        return _STRATEGIES[mode]()
    except KeyError:
        raise ValueError(f"Noma'lum qidiruv rejimi: {mode}") from None
