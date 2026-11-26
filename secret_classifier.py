import json
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

DATA_PATH = Path("data.json")
MODEL_PATH = Path("models/secret_model.joblib")


def train():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    texts = [item["text"] for item in data]
    labels = [item["label"] for item in data]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf", LogisticRegression(class_weight="balanced", random_state=42))
    ])

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    print("=== Отчёт по качеству модели ===")
    print(classification_report(y_test, predictions, zero_division=0))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Готово! Модель сохранена в файл: {MODEL_PATH}")


_loaded_model = None


def classify_secret(text: str, threshold: float = 0.55) -> int:
    global _loaded_model
    if _loaded_model is None:
        _loaded_model = joblib.load(MODEL_PATH)

    probs = _loaded_model.predict_proba([text])
    probability = probs[0][1]

    if probability >= threshold:
        return 1
    return 0


if __name__ == "__main__":
    train()
    print("\n--- Проверка на новых фразах ---")
    print("Тест 1 (ожидаем 1):", classify_secret("Себестоимость партии 100 рублей"))
    print("Тест 2 (ожидаем 0):", classify_secret("Пойдём пить кофе на обеде"))
