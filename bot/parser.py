"""
Чистая функция парсинга текста поста на гороскопы по знакам.
Не имеет побочных эффектов и внешних зависимостей — легко тестируется (см. tests/test_parser.py).
"""
import re

SIGN_ICONS = {
    "Овен": "♈️", "Телец": "♉️", "Близнецы": "♊️",
    "Рак": "♋️", "Лев": "♌️", "Дева": "♍️",
    "Весы": "♎️", "Скорпион": "♏️", "Стрелец": "♐️",
    "Козерог": "♑️", "Водолей": "♒️", "Рыбы": "♓️"
}
SIGN_NAMES = list(SIGN_ICONS.keys())


def parse_horoscope(text: str) -> dict:
    if not text:
        return {}
    horoscopes = {}
    names_pattern = "|".join(SIGN_NAMES)
    for name in SIGN_NAMES:
        pattern = rf"{name}\s*:\s*(.+?)(?=(?:[^\w]*(?:{names_pattern})\s*:)|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            horoscopes[name] = match.group(1).strip()
    return horoscopes


def format_horoscope_answer(name: str, text: str) -> str:
    icon = SIGN_ICONS.get(name, "")
    return f"{icon}{name}:\n\n{text}"
