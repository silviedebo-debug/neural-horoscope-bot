"""
Тесты чистой функции parse_horoscope — не требуют сети, Telegram или Apify.
Запуск: python -m pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.parser import parse_horoscope, format_horoscope_answer, SIGN_ICONS


SAMPLE_POST = (
    "♑️Овен : Не исключены приступы диареи под предлогом борьбы с капитализмом. "
    "Хорошее время для того, чтобы скрещивать зубы.\n"
    "♒️Телец : Возможно, вам захочется устроить революцию на кухне.\n"
    "♓️Близнецы : День подходит для смены имиджа и переезда в другую галактику."
)


def test_parses_known_signs():
    result = parse_horoscope(SAMPLE_POST)
    assert "Овен" in result
    assert "Телец" in result
    assert "Близнецы" in result


def test_extracts_correct_text_without_bleeding_into_next_sign():
    result = parse_horoscope(SAMPLE_POST)
    assert "Телец" not in result["Овен"]
    assert "Близнецы" not in result["Телец"]


def test_empty_text_returns_empty_dict():
    assert parse_horoscope("") == {}
    assert parse_horoscope(None) == {}


def test_text_with_no_matching_signs_returns_empty_dict():
    assert parse_horoscope("Случайный текст без знаков зодиака") == {}


def test_format_horoscope_answer_includes_icon():
    answer = format_horoscope_answer("Овен", "тестовый текст")
    assert answer.startswith(SIGN_ICONS["Овен"])
    assert "тестовый текст" in answer


if __name__ == "__main__":
    test_parses_known_signs()
    test_extracts_correct_text_without_bleeding_into_next_sign()
    test_empty_text_returns_empty_dict()
    test_text_with_no_matching_signs_returns_empty_dict()
    test_format_horoscope_answer_includes_icon()
    print("Все тесты прошли успешно ✅")
