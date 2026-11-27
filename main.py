from contextlib import asynccontextmanager
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fusion import analyze


MODEL_PATH = Path("models/secret_model.joblib")
DATA_PATH = Path("data.json")


def _warmup():
    try:
        from ner_extractor import _load
        _load()
        print("[warmup] NER загружен")
    except Exception as e:
        print(f"[warmup] NER не загружен: {e}")

    try:
        import secret_classifier
        if not MODEL_PATH.exists() and DATA_PATH.exists():
            print("[warmup] Модель классификатора не найдена — обучаю...")
            secret_classifier.train()
        if secret_classifier._loaded_model is None and MODEL_PATH.exists():
            secret_classifier._loaded_model = joblib.load(MODEL_PATH)
            print("[warmup] Классификатор загружен")
    except Exception as e:
        print(f"[warmup] Классификатор не загружен: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _warmup()
    yield


app = FastAPI(title="DLP Service", version="1.0.0", lifespan=lifespan)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1)


class Entity(BaseModel):
    type: str
    start: int
    end: int
    text: str
    confidence: float


class AnalyzeResponse(BaseModel):
    text: str
    is_secret: int
    secret_probability: float
    entities: list[Entity]


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(req: AnalyzeRequest):
    try:
        result = analyze(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {e}")
    return AnalyzeResponse(text=req.text, **result)


@app.get("/")
def root():
    return {
        "service": "DLP Service",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}
