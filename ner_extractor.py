import re
import spacy

_nlp = None

# Правило для полных адресов (формат faker.ru): "г. Москва, ул. Ленина, д. 5, кв. 10"
ADDRESS_RE = re.compile(
    r"г\.\s*[А-ЯЁ][а-яё\-]*(?:\s+[А-ЯЁ][а-яё\-]*)*"
    r"(?:,\s*(?:ул\.|пер\.|пр-т\.|пр\.|б-р\.|пл\.|наб\.)\s*[^,;\n]+)?"
    r"(?:,\s*д\.\s*\d+(?:\s*,?\s*кв\.\s*\d+)?)?",
)

LABEL_MAP = {
    "PER": "PERSON",
    "PERSON": "PERSON",
    "LOC": "LOCATION",
    "ORG": "ORG",
}


def _load():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("ru_core_news_sm")
        except OSError as e:
            raise RuntimeError(
                "spaCy-модель 'ru_core_news_sm' не установлена. "
                "Установка: python -m spacy download ru_core_news_sm"
            ) from e
    return _nlp


def extract_ner(text: str) -> list[dict]:
    nlp = _load()
    doc = nlp(text)
    findings = []

    for ent in doc.ents:
        mapped = LABEL_MAP.get(ent.label_)
        if not mapped:
            continue
        findings.append({
            "type": mapped,
            "start": ent.start_char,
            "end": ent.end_char,
            "text": ent.text,
            "confidence": 0.85,
        })

    # Достаём полные адреса правилом (spaCy даёт только LOC — город)
    for m in ADDRESS_RE.finditer(text):
        findings.append({
            "type": "ADDRESS",
            "start": m.start(),
            "end": m.end(),
            "text": m.group(0),
            "confidence": 0.75,
        })

    return findings


if __name__ == "__main__":
    sample = "Клиент Иван Иванов, г. Москва, ул. Ленина, д. 5, кв. 10, просит перезвонить."
    for e in extract_ner(sample):
        print(e)