"""Yordamchi funksiyalar: matnni normallashtirish va caption tahlili."""
import re

_APOSTROPHES = str.maketrans(
    {"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "´": "'"}
)


def normalize(text: str) -> str:
    """Qidiruv uchun: kichik harf, bir xil apostrof (o', g'), ortiqcha bo'shliqsiz.

    SQLite LIKE faqat ASCII uchun harf registrini e'tiborsiz qoldiradi,
    shuning uchun normallashtirishni Python tomonida bajaramiz.
    """
    text = (text or "").translate(_APOSTROPHES).lower().strip()
    return re.sub(r"\s+", " ", text)


def escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def parse_book_meta(caption: str | None, file_name: str | None) -> tuple[str, str, str]:
    """Caption formati: 'Nomi | Muallif | Janr'. Bo'lmasa fayl nomidan olinadi."""
    stem = re.sub(r"\.pdf$", "", file_name or "", flags=re.I).replace("_", " ").strip()
    title, author, genre = stem, "Noma'lum", "Umumiy"
    if caption and caption.strip():
        parts = [p.strip() for p in caption.strip().splitlines()[0].split("|")]
        if parts[0]:
            title = parts[0]
        if len(parts) > 1 and parts[1]:
            author = parts[1]
        if len(parts) > 2 and parts[2]:
            genre = parts[2]
    return title or "Nomsiz kitob", author, genre
