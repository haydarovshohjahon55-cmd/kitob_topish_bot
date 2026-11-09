"""Telegram interfeysi (presentation qatlami). Biznes mantiq services.py da."""
import functools
import html
import logging

from telebot import types

from app.container import AppContext
from app.services import BookNotFound
from app.utils import parse_book_meta

logger = logging.getLogger(__name__)

BTN_ALL = "📚 Umumiy qidiruv"
BTN_TITLE = "📖 Nomi bo‘yicha"
BTN_AUTHOR = "👤 Muallif bo‘yicha"
BTN_LATEST = "🆕 Yangi kitoblar"
MENU_MODES = {BTN_ALL: "all", BTN_TITLE: "title", BTN_AUTHOR: "author"}
PROMPTS = {
    "all": "Kitob nomi, muallif yoki janrni yozing:",
    "title": "Kitob nomini yozing:",
    "author": "Muallif ismini yozing:",
}
esc = html.escape


def main_menu() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(BTN_ALL, BTN_LATEST)
    kb.row(BTN_TITLE, BTN_AUTHOR)
    return kb


def render_page(page, mode: str, query: str):
    if mode == "latest":
        header = "🆕 <b>So‘nggi kitoblar</b>"
    else:
        header = f"🔎 <b>{esc(query)}</b>"
    lines = [f"{header} — {page.total} ta natija (sahifa {page.page}/{page.pages})\n"]
    markup = types.InlineKeyboardMarkup()
    for i, b in enumerate(page.items, start=page.offset + 1):
        lines.append(f"{i}. <b>{esc(b.title)}</b>\n    👤 {esc(b.author)} · 🏷 {esc(b.genre)}")
        markup.add(types.InlineKeyboardButton(f"📥 {i}. {b.title}"[:60], callback_data=f"b:{b.id}"))
    nav = []
    if page.page > 1:
        nav.append(types.InlineKeyboardButton("⬅️ Oldingi", callback_data=f"p:{page.page - 1}"))
    if page.page < page.pages:
        nav.append(types.InlineKeyboardButton("Keyingi ➡️", callback_data=f"p:{page.page + 1}"))
    if nav:
        markup.row(*nav)
    return "\n".join(lines), markup


def register_handlers(bot, ctx: AppContext) -> None:
    s = ctx.settings

    # --- Consumer: yangi kitob qo'shilganda adminlarga xabar (L9) ---
    from app.events import BookAdded

    def notify_admins(event: BookAdded):
        for admin_id in ctx.users.admin_ids_all():
            try:
                bot.send_message(admin_id, f"✅ Bazaga qo‘shildi: #{event.book.id} {event.book.title}")
            except Exception:
                logger.warning("Adminga (%s) xabar yuborib bo'lmadi", admin_id)

    ctx.events.subscribe(BookAdded, notify_admins)

    # --- Dekorator: foydalanuvchini ro'yxatga olish, ruxsat, xatolik, vaqt o'lchash ---
    def guarded(admin: bool = False):
        def deco(fn):
            @functools.wraps(fn)
            def wrapper(obj):
                user = obj.from_user
                chat_id = obj.chat.id if hasattr(obj, "chat") else obj.message.chat.id
                ctx.metrics.incr(f"handler.{fn.__name__}")
                try:
                    with ctx.metrics.timer(f"handler.{fn.__name__}"):
                        ctx.users.register(user.id, user.username, user.full_name)
                        if admin and not ctx.users.is_admin(user.id):
                            ctx.metrics.incr("auth.denied")
                            logger.warning("Ruxsat rad etildi: user=%s cmd=%s", user.id, fn.__name__)
                            bot.send_message(chat_id, "⛔ Bu amal faqat adminlar uchun.")
                            return
                        fn(obj)
                except Exception:
                    ctx.metrics.incr("errors")
                    logger.exception("Handler xatosi: %s", fn.__name__)
                    try:
                        bot.send_message(chat_id, "⚠️ Xatolik yuz berdi. Keyinroq urinib ko‘ring.")
                    except Exception:
                        pass
            return wrapper
        return deco

    def run_search(chat_id, user_id, mode, query, page=1, edit=None):
        try:
            result = ctx.books.search(mode, query, page, user_id=user_id)
        except ValueError as e:
            bot.send_message(chat_id, f"❗ {e}")
            return
        ctx.state[user_id] = {"mode": mode, "query": query}
        if result.total == 0:
            bot.send_message(chat_id, "😕 Hech narsa topilmadi. Boshqa so‘z bilan urinib ko‘ring.")
            return
        text, markup = render_page(result, mode, query)
        if edit:
            bot.edit_message_text(text, chat_id, edit, parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

    # ---------------- Foydalanuvchi buyruqlari ----------------
    @bot.message_handler(commands=["start", "help"])
    @guarded()
    def start(msg):
        ctx.state[msg.from_user.id] = {"mode": "all", "query": ""}
        bot.send_message(
            msg.chat.id,
            "📚 <b>Kitob qidiruv boti</b>\n\n"
            "Kitob nomi, muallif yoki janrni yozing — men PDF variantini yuboraman.\n"
            "Pastdagi menyudan qidiruv turini ham tanlashingiz mumkin.",
            parse_mode="HTML", reply_markup=main_menu(),
        )

    @bot.message_handler(commands=["latest"])
    @guarded()
    def latest(msg):
        run_search(msg.chat.id, msg.from_user.id, "latest", "")

    # ---------------- Admin buyruqlari ----------------
    @bot.message_handler(commands=["stats"])
    @guarded(admin=True)
    def stats(msg):
        books, downloads = ctx.books.stats()
        top = ctx.searches.top_queries(5)
        top_text = "\n".join(f"  • {esc(q)} — {c}" for q, c in top) or "  —"
        bot.send_message(
            msg.chat.id,
            f"📊 <b>Statistika</b>\nFoydalanuvchilar: {ctx.users.count()}\n"
            f"Kitoblar: {books}\nYuklab olishlar: {downloads}\n\n"
            f"Ko‘p qidirilganlar:\n{top_text}",
            parse_mode="HTML",
        )

    @bot.message_handler(commands=["metrics"])
    @guarded(admin=True)
    def metrics(msg):
        bot.send_message(msg.chat.id, ctx.metrics.report())

    @bot.message_handler(commands=["delbook"])
    @guarded(admin=True)
    def delbook(msg):
        parts = msg.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            bot.send_message(msg.chat.id, "Foydalanish: /delbook <id>")
            return
        ok = ctx.books.delete(int(parts[1]))
        bot.send_message(msg.chat.id, "🗑 O‘chirildi." if ok else "Bunday kitob yo‘q.")

    @bot.message_handler(commands=["addadmin"])
    @guarded(admin=True)
    def addadmin(msg):
        parts = msg.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            bot.send_message(msg.chat.id, "Foydalanish: /addadmin <user_id>")
            return
        ok = ctx.users.make_admin(int(parts[1]))
        bot.send_message(
            msg.chat.id,
            "✅ Admin qilindi." if ok else "Foydalanuvchi botga hali /start bosmagan.",
        )

    # Admin botga PDF yuborsa: kanalga joylanadi va bazaga yoziladi
    @bot.message_handler(content_types=["document"], func=lambda m: m.chat.type == "private")
    @guarded(admin=True)
    def admin_upload(msg):
        doc = msg.document
        if not _is_pdf(doc):
            bot.send_message(msg.chat.id, "Faqat PDF fayl qabul qilinadi.")
            return
        title, author, genre = parse_book_meta(msg.caption, doc.file_name)
        caption = f"{title} | {author} | {genre}"
        sent = bot.send_document(s.channel_id, doc.file_id, caption=caption)
        book = ctx.books.add_from_channel(
            title=title, author=author, genre=genre, file_id=sent.document.file_id,
            file_name=doc.file_name or "", file_size=doc.file_size or 0,
            channel_id=s.channel_id, message_id=sent.message_id,
        )
        if not book:
            bot.send_message(msg.chat.id, "Bu kitob allaqachon bazada bor.")

    # ---------------- Kanal postlari ----------------
    @bot.channel_post_handler(content_types=["document"])
    def on_channel_document(msg):
        if msg.chat.id != s.channel_id:
            return
        try:
            doc = msg.document
            if not _is_pdf(doc):
                return
            title, author, genre = parse_book_meta(msg.caption, doc.file_name)
            ctx.books.add_from_channel(
                title=title, author=author, genre=genre, file_id=doc.file_id,
                file_name=doc.file_name or "", file_size=doc.file_size or 0,
                channel_id=msg.chat.id, message_id=msg.message_id,
            )
        except Exception:
            ctx.metrics.incr("errors")
            logger.exception("Kanal postini qayta ishlashda xatolik")

    # ---------------- Matnli qidiruv ----------------
    @bot.message_handler(content_types=["text"], func=lambda m: not m.text.startswith("/"))
    @guarded()
    def on_text(msg):
        uid, text = msg.from_user.id, msg.text.strip()
        if text == BTN_LATEST:
            run_search(msg.chat.id, uid, "latest", "")
        elif text in MENU_MODES:
            mode = MENU_MODES[text]
            ctx.state[uid] = {"mode": mode, "query": ""}
            bot.send_message(msg.chat.id, PROMPTS[mode])
        else:
            mode = ctx.state.get(uid, {}).get("mode", "all")
            run_search(msg.chat.id, uid, mode, text)

    # ---------------- Inline tugmalar ----------------
    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("p:"))
    @guarded()
    def on_page(call):
        st = ctx.state.get(call.from_user.id)
        if not st:
            bot.answer_callback_query(call.id, "Qidiruv eskirgan, qaytadan yozing.", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        run_search(call.message.chat.id, call.from_user.id, st["mode"], st["query"],
                   page=int(call.data[2:]), edit=call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("b:"))
    @guarded()
    def on_book(call):
        try:
            book = ctx.books.download(int(call.data[2:]), call.from_user.id)
        except BookNotFound:
            bot.answer_callback_query(call.id, "Kitob topilmadi.", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Yuborilmoqda...")
        try:
            bot.send_document(
                call.message.chat.id, book.file_id,
                caption=f"📖 {book.title}\n👤 {book.author}\n🏷 {book.genre}",
            )
        except Exception:
            ctx.metrics.incr("errors.send_document")
            logger.exception("Faylni yuborib bo'lmadi: book=%s", book.id)
            bot.send_message(call.message.chat.id, "⚠️ Faylni yuborib bo‘lmadi.")


def _is_pdf(doc) -> bool:
    return doc.mime_type == "application/pdf" or (doc.file_name or "").lower().endswith(".pdf")
