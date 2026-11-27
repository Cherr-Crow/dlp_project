
import re

def is_valid_snils(snils_str: str) -> bool:
    """ СНИЛС."""
    digits = [int(c) for c in snils_str if c.isdigit()]
    if len(digits) != 11:
        return False

    # Номера меньше 001-001-998 не проверяются по алгоритму
    number_part = int("".join(map(str, digits[:9])))
    if number_part <= 1001998:
        return True

    checksum = sum(digits[i] * (9 - i) for i in range(9))
    if checksum < 100:
        expected = checksum
    elif checksum in (100, 101):
        expected = 0
    else:
        expected = checksum % 101
        if expected == 100:
            expected = 0

    return expected == int(f"{digits[9]}{digits[10]}")


def is_valid_inn(inn_str: str) -> bool:
    """ИНН (10 цифр — юрлица, 12 — физлица)."""
    digits = [int(c) for c in inn_str if c.isdigit()]

    if len(digits) == 10:
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        check = sum(digits[i] * weights[i] for i in range(9)) % 11 % 10
        return check == digits[9]

    elif len(digits) == 12:
        weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        check1 = sum(digits[i] * weights1[i] for i in range(10)) % 11 % 10
        check2 = sum(digits[i] * weights2[i] for i in range(11)) % 11 % 10
        return check1 == digits[10] and check2 == digits[11]

    return False


def is_valid_card(card_str: str) -> bool:
    """ банковская карта (16 цифр) по алгоритму Луна."""
    digits = [int(c) for c in card_str if c.isdigit()]
    if len(digits) != 16:
        return False

    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0


def has_passport_context(text: str, start: int, end: int, window: int = 40) -> bool:
    """ паспорта  """
    left_border = max(0, start - window)
    right_border = min(len(text), end + window)
    context = text[left_border:right_border].lower()
    keywords = ("паспорт", "серия", "номер", "выдан", "кем выдан", "паспортные")
    return any(word in context for word in keywords)


PATTERNS = {
    "PASSPORT": r"\b\d{2}\s?\d{2}\s?\d{6}\b",
    "SNILS": r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}\b",
    "INN": r"\b(?:\d{10}|\d{12})\b",
    "BANK_CARD": r"\b(?:\d{4}[\s\-]?){3}\d{4}\b",
    "PHONE": r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b",
    "EMAIL": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    
    "SECRET": (
        r"(?:\b(?:sk-[a-zA-Z0-9\-_]{16,}|ghp_[a-zA-Z0-9]{20,})\b"
        r"|(?:postgres|postgresql|mysql|mongodb|redis)://[^\s'\"<>]+"
        r"|(?:password|passwd|secret|api_key)\s*[:=]\s*['\"][^'\"]+['\"])"
    ),

    # 1. Грифы коммерческой тайны (98-ФЗ)
    "NDA_MARKER": r"(?i)\b(?:коммерческ\w+\s+тайн\w*|строго\s+конфиденциально|конфиденциально|nda|дсп|для\s+служебного\s+пользования)\b",

    # 2. Непубличные финансовые данные (финансовый контекст + цифры/проценты)
    "FINANCIAL_DATA": r"(?i)\b(?:выручка|прибыль|убыток|бюджет|себестоимость|маржа|оборот)\s*(?:составил[ао]?|равн[ао]|—|-|:)?\s*\d+(?:[.,]\d+)?\s*(?:млн|млрд|тыс\.?|руб\.?|₽|%)",
}



#  ГЛАВНАЯ ФУНКЦИЯ ПОИСКА 

def extract_regex(text: str) -> list[dict]:
   
    findings = []

    for entity_type, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            found_text = match.group(0)
            start_idx = match.start()
            end_idx = match.end()

            if entity_type == "PASSPORT" and not has_passport_context(text, start_idx, end_idx):
                continue
            if entity_type == "SNILS" and not is_valid_snils(found_text):
                continue
            if entity_type == "INN" and not is_valid_inn(found_text):
                continue
            if entity_type == "BANK_CARD" and not is_valid_card(found_text):
                continue

            findings.append({
                "type": entity_type,
                "start": start_idx,
                "end": end_idx,
                "text": found_text,
                "confidence": 1.0
            })

    return findings



# ТЕСТОВЫЙ ЗАПУСК (ДЛЯ ПРОВЕРКИ РАБОТЫ)

if __name__ == "__main__":
    test_prompt = (
        "Гриф: Коммерческая тайна. Подготовь отчёт по ООО Ромашка (ИНН 7707083893). "
        "Выручка 15 млн руб., маржа 24%. Контакт директора: +7 (999) 123-45-67, "
        "ivanov@company.ru, паспорт 45 06 123456, СНИЛС 112-233-445 95. "
        "Подключение к БД: postgres://admin:qwerty@10.0.0.5:5432/prod_db"
    )

    print("Найдены следующие сущности:\n")
    for entity in extract_regex(test_prompt):
        print(entity)
