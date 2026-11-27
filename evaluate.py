import json
import statistics
import time
from collections import defaultdict
from pathlib import Path

from fusion import analyze


DATA_PATH = Path("data.json")
SECRET_TYPES = {"SECRET", "FINANCIAL_DATA", "NDA_MARKER"}


def _find_span(text: str, entity_text: str):
    idx = text.find(entity_text)
    if idx < 0:
        return None
    return (idx, idx + len(entity_text))


def _overlap(gt, pred, min_ratio=0.5) -> bool:
    if pred[0] >= gt[1] or pred[1] <= gt[0]:
        return False
    inter = min(gt[1], pred[1]) - max(gt[0], pred[0])
    return inter / max(1, gt[1] - gt[0]) >= min_ratio


def _is_whole_text(ent: dict, text_len: int, ratio: float = 0.8) -> bool:
    return (ent["end"] - ent["start"]) >= ratio * text_len


def _print_metrics(tp, fp, fn, indent=""):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    print(f"{indent}TP={tp} FP={fp} FN={fn}")
    print(f"{indent}Precision={precision:.3f} Recall={recall:.3f} F1={f1:.3f}")


def evaluate():
    if not DATA_PATH.exists():
        raise FileNotFoundError("data.json не найден. Сначала запусти data_gen.py")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    tp_total = fp_total = fn_total = 0
    per_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    times: list[float] = []

    secret_tp = secret_fp = secret_fn = 0

    for sample in data:
        text = sample["text"]
        gt_entities = sample["entities"]

        t0 = time.perf_counter()
        result = analyze(text)
        times.append(time.perf_counter() - t0)

        # Исключаем «флаг» SECRET на весь текст из entity-метрик
        pred_entities = [
            e for e in result["entities"]
            if not (e["type"] == "SECRET" and _is_whole_text(e, len(text)))
        ]

        gt_spans = []
        for gt in gt_entities:
            span = _find_span(text, gt["text"])
            if span is None:
                continue
            gt_spans.append((gt["type"], span))

        matched_gt, matched_pred = set(), set()

        for i, (gt_type, gt_span) in enumerate(gt_spans):
            for j, pred in enumerate(pred_entities):
                if j in matched_pred or pred["type"] != gt_type:
                    continue
                if _overlap(gt_span, (pred["start"], pred["end"])):
                    matched_gt.add(i)
                    matched_pred.add(j)
                    break

        tp = len(matched_gt)
        fn = len(gt_spans) - tp
        fp = len(pred_entities) - len(matched_pred)

        tp_total += tp
        fn_total += fn
        fp_total += fp

        for i, (gt_type, _) in enumerate(gt_spans):
            per_type[gt_type]["tp" if i in matched_gt else "fn"] += 1
        for j, pred in enumerate(pred_entities):
            if j not in matched_pred:
                per_type[pred["type"]]["fp"] += 1

        gt_secret = any(e["type"] in SECRET_TYPES for e in gt_entities)
        pred_secret = result["is_secret"] == 1
        if gt_secret and pred_secret:
            secret_tp += 1
        elif pred_secret and not gt_secret:
            secret_fp += 1
        elif gt_secret and not pred_secret:
            secret_fn += 1

    print("=" * 60)
    print("ОБЩИЕ МЕТРИКИ (entity-level)")
    print("=" * 60)
    _print_metrics(tp_total, fp_total, fn_total)

    print("\n" + "=" * 60)
    print("МЕТРИКИ ПО ТИПАМ")
    print("=" * 60)
    for t in sorted(per_type):
        print(f"\n[{t}]")
        m = per_type[t]
        _print_metrics(m["tp"], m["fp"], m["fn"], indent="  ")

    print("\n" + "=" * 60)
    print("TEXT-LEVEL SECRET DETECTION (классификатор)")
    print("=" * 60)
    _print_metrics(secret_tp, secret_fp, secret_fn)

    print("\n" + "=" * 60)
    print("СКОРОСТЬ")
    print("=" * 60)
    print(f"  Среднее: {statistics.mean(times)*1000:.2f} мс")
    print(f"  Медиана: {statistics.median(times)*1000:.2f} мс")
    print(f"  Максимум: {max(times)*1000:.2f} мс")
    print(f"  Всего записей: {len(data)}")


if __name__ == "__main__":
    evaluate()