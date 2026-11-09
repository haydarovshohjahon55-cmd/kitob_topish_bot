from app.utils import normalize, parse_book_meta


def test_normalize_apostrophes_and_case():
    assert normalize("  O‘zbek   ADABIYOTI ") == "o'zbek adabiyoti"
    assert normalize("Go`zal") == "go'zal"


def test_parse_caption_full():
    assert parse_book_meta("O‘tkan kunlar | Abdulla Qodiriy | Roman", "x.pdf") == (
        "O‘tkan kunlar", "Abdulla Qodiriy", "Roman")


def test_parse_without_caption_uses_filename():
    assert parse_book_meta(None, "Mehrobdan_chayon.pdf") == (
        "Mehrobdan chayon", "Noma'lum", "Umumiy")


def test_parse_partial_caption():
    assert parse_book_meta("Sariq devni minib | Xudoyberdi", "a.pdf") == (
        "Sariq devni minib", "Xudoyberdi", "Umumiy")
