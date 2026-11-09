"""Konfiguratsiya koddan ajratilgan: barcha sozlamalar .env dan o'qiladi (L2)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    token: str
    channel_id: int
    admin_ids: frozenset
    db_path: str = "data/books.db"
    page_size: int = 5
    log_level: str = "INFO"


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylini tekshiring.")
    channel_raw = os.getenv("CHANNEL_ID", "").strip()
    if not channel_raw.lstrip("-").isdigit():
        raise RuntimeError("CHANNEL_ID son bo'lishi kerak (masalan -1001234567890).")
    admins = frozenset(
        int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
    )
    return Settings(
        token=token,
        channel_id=int(channel_raw),
        admin_ids=admins,
        db_path=os.getenv("DB_PATH", "data/books.db"),
        page_size=int(os.getenv("PAGE_SIZE", "5")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
