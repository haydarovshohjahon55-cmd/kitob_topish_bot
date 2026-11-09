import logging

from app.logger import RedactFilter


def test_token_is_redacted():
    rec = logging.LogRecord("x", logging.INFO, "", 0,
                            "url https://api/bot123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw9/getMe", (), None)
    RedactFilter().filter(rec)
    assert "AAHdq" not in rec.getMessage()
