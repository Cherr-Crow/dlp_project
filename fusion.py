from regex_extractor import extract_regex
from ner_extractor import extract_ner


SECRET_TYPES = {"SECRET", "FINANCIAL_DATA", "NDA_MARKER"}


def _secret_probability(text: str) -> float:
    """Достаёт вероятность класса '1' из обученного классификатора."""
    try:
        import joblib
        import secret_classifier
        if secret_classifier._loaded_model is None:
            if not secret_classifier.MODEL_PATH.exists():
                return 0.0
            secret_classifier._loaded_model = joblib.load(secret_classifier.MODEL_PATH)
        return float(secret_classifier._loaded_model.predict_proba([text])[0][1])
    except Exception:
        return 0.0


def unique_and_sorted(findings: list[dict]) -> list[dict]:
    """Убирает пересечения сущностей одного типа, сортирует по start."""
    by_type: dict[str, list[dict]] = {}
    for f in findings:
        by_type.setdefault(f["type"], []).append(f)

    result: list[dict] = []
    for items in by_type.values():
        items.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
        kept: list[dict] = []
        for f in items:
            if kept and f["start"] < kept[-1]["end"]:
                prev = kept[-1]
                if (f["confidence"], f["end"] - f["start"]) > (prev["confidence"], prev["end"] - prev["start"]):
                    kept[-1] = f
            else:
                kept.append(f)
        result.extend(kept)

    result.sort(key=lambda x: (x["start"], x["end"]))
    return result


def analyze(text: str, threshold: float = 0.55) -> dict:
    findings: list[dict] = []
    findings += extract_regex(text)
    findings += extract_ner(text)

    prob = _secret_probability(text)
    is_secret = prob >= threshold

    # Если классификатор сработал и regex ничего специфичного не нашёл —
    # добавляем «флаг» SECRET на весь текст.
    if is_secret and not any(f["type"] in SECRET_TYPES for f in findings):
        findings.append({
            "type": "SECRET",
            "start": 0,
            "end": len(text),
            "text": text,
            "confidence": round(prob, 2),
        })

    return {
        "entities": unique_and_sorted(findings),
        "is_secret": int(is_secret),
        "secret_probability": round(prob, 4),
    }


if __name__ == "__main__":
    import json
    sample = (
        "Гриф: Коммерческая тайна. Подготовь отчёт по ООО Ромашка (ИНН 7707083893). "
        "Выручка 15 млн руб., маржа 24%. Контакт директора: +7 (999) 123-45-67, "
        "ivanov@company.ru, паспорт 45 06 123456, СНИЛС 112-233-445 95."
    )
    print(json.dumps(analyze(sample), ensure_ascii=False, indent=2))