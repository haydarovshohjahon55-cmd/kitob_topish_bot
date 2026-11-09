"""Jurnal yuritish. Token kabi maxfiy ma'lumotlar loglarga tushmaydi (L14)."""
import logging
import os
import re
from logging.handlers import RotatingFileHandler

_SECRET = re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}")


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if _SECRET.search(message):
            record.msg = _SECRET.sub("***TOKEN***", message)
            record.args = ()
        return True


def setup_logging(level: str = "INFO", log_dir: str = "logs") -> None:
    os.makedirs(log_dir, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    file_h = RotatingFileHandler(
        os.path.join(log_dir, "bot.log"), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    root = logging.getLogger()
    root.setLevel(level)
    for h in (console, file_h):
        h.setFormatter(fmt)
        h.addFilter(RedactFilter())
        root.addHandler(h)
