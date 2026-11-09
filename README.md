# 📚 Kitob qidiruv Telegram boti

Fan: *Dasturiy ta’minot tizimlarini loyihalash* (L1–L15 laboratoriya mavzulari asosida).
Bitta **bot** + bitta **kanal** (PDF kitoblar), baza — **SQLite**, kutubxona — **pyTelegramBotAPI**.

## Ishlash prinsipi
1. Kanalga PDF joylanadi (caption: `Kitob nomi | Muallif | Janr`).
2. Bot kanalda **admin** bo‘lgani uchun postni ko‘radi va metama’lumotni SQLite ga yozadi.
3. Foydalanuvchi botga nom/muallif/janr yozadi → natijalar tugmalar bilan chiqadi → tugmani bosganda PDF yuboriladi.

Qo‘shimcha: admin PDF ni **botga shaxsiy xabarda** yuborsa, bot uni o‘zi kanalga joylaydi va bazaga yozadi.

## Ishga tushirish
```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # va to'ldiring
python bot.py
```
**.env**: `BOT_TOKEN` (@BotFather), `CHANNEL_ID` (masalan `-1001234567890`), `ADMIN_IDS` (o‘zingizning Telegram ID, @userinfobot orqali).

**Kanalni ulash:** kanal yarating → botni kanalga **administrator** qilib qo‘shing (post o‘qish/yuborish huquqi bilan). Kanal ID sini bilish uchun kanalga biror post yuborib, uni @RawDataBot ga forward qiling.

> Eslatma: bot kanaldagi **eski** postlarni o‘qiy olmaydi. Eski PDF larni kanalga qayta yuboring yoki botga admin sifatida yuboring.

Docker: `docker compose up -d --build`

## Buyruqlar
| Buyruq | Kim uchun | Vazifa |
|---|---|---|
| `/start`, `/help` | hamma | Menyu |
| `/latest` | hamma | So‘nggi kitoblar |
| matn yozish | hamma | Qidiruv (nom, muallif, janr) |
| `/stats` | admin | Statistika, ko‘p qidirilganlar |
| `/metrics` | admin | Handlerlar soni, javob vaqti, xatolar |
| `/delbook <id>` | admin | Kitobni bazadan o‘chirish |
| `/addadmin <id>` | admin | Admin tayinlash |

## Testlar
```bash
pip install -r requirements-dev.txt
pytest -q
```

## Laboratoriya mavzulari bilan bog‘liqligi
| Lab | Qayerda |
|---|---|
| L1 Git | Git repo, feature branchlar (`git init`) |
| L2 Struktura | `app/`, `tests/`, `config.py`, `.env`, README |
| L3 Clean/Hexagonal | `repositories.py` (port = ABC, adapter = Sqlite…), `services.py`, `container.py` (DI) |
| L4 Domen/Servis | `models.py`, `BookService`, `UserService`, `BookRepository` |
| L5 Patternlar | `search.py` (Strategy + Factory), Dependency Injection |
| L6/L7 REST va hujjat | Bot — interfeys; kerak bo‘lsa FastAPI qo‘shib, `BookService` ni qayta ishlatish mumkin |
| L8 DB | `database.py` — migratsiyalar (`user_version`), tranzaksiya (commit/rollback), UNIQUE, FK |
| L9 Event-driven | `events.py` — `BookAdded`, `BookDownloaded`, `SearchPerformed` |
| L10 Docker | `Dockerfile`, `docker-compose.yml` |
| L11 Testlar | `tests/` — unit (mock) va integration (haqiqiy SQLite) |
| L12 CI | `.github/workflows/ci.yml` |
| L13 Auth | Rollar `user/admin`, `guarded(admin=True)` dekoratori |
| L14 Logging/Monitoring | `logger.py` (token yashiriladi), `metrics.py`, `/metrics` |
| L15 Integratsiya | Barcha komponentlar `bot.py` da birlashadi |
