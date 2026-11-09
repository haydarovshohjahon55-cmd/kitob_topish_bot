"""Kirish nuqtasi: sozlamalar -> log -> kontekst -> handlerlar -> polling."""
import logging

import telebot
from telebot import types

from app.container import build_context
from app.handlers import register_handlers
from app.logger import setup_logging
from config import load_settings

logger = logging.getLogger("bot")


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    ctx = build_context(settings)

    bot = telebot.TeleBot(settings.token, threaded=True)
    register_handlers(bot, ctx)
    bot.set_my_commands([
        types.BotCommand("start", "Botni ishga tushirish"),
        types.BotCommand("latest", "So‘nggi kitoblar"),
        types.BotCommand("help", "Yordam"),
    ])
    logger.info("Bot ishga tushdi")
    bot.infinity_polling(
        timeout=30, long_polling_timeout=30,
        allowed_updates=["message", "callback_query", "channel_post"],
    )


if __name__ == "__main__":
    main()
