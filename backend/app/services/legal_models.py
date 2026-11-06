"""
Hooks for the three legal-document models.

Summaries use the LexRank implementation in lexRank.py.
Outcome prediction loads the .joblib classifier placed in this folder.
TF-IDF cosine similarity is not implemented here.
"""

import math
from pathlib import Path

import joblib
import numpy as np
from fastapi import HTTPException

from app.schemas.analysis import (
    PredictionResult,
    SimilarCasesResult,
    SummaryResult,
)
from app.services.lexRank import lexrank_summarize as run_lexrank

SERVICE_DIR = Path(__file__).resolve().parent
ACCEPTED_LABELS = {
    "1",
    "accepted",
    "accept",
    "allowed",
    "allow",
    "granted",
    "grant",
    "upheld",
    "yes",
    "true",
    "positive",
}
REJECTED_LABELS = {
    "0",
    "rejected",
    "reject",
    "dismissed",
    "dismiss",
    "denied",
    "deny",
    "no",
    "false",
    "negative",
}
_model = None
_model_stamp = None

SUMMARY_SENTENCES = 5


def lexrank_summarize(text):
    sentences = run_lexrank(
        text,
        num_sentences=SUMMARY_SENTENCES,
        clean_citations=True,
        strip_headers=True,
    )
    summary = " ".join(sentence.strip() for sentence in sentences if sentence.strip())

    return SummaryResult(
        implemented=True,
        summary=summary or None,
        sentences=sentences,
    )


def recommend_similar_cases(text, library, top_k=5):
    return SimilarCasesResult(
        requested=top_k,
        cases=[]
    )


def predict_outcome(text):
    model = _load_outcome_model()
    if model is None:
        return PredictionResult()

    try:
        label = model.predict([text])[0]
        outcome = _to_outcome(label)
        confidence = _confidence(model, text, label)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The outcome model could not score this document. It needs to accept the case text directly, usually as a scikit-learn pipeline saved in one .joblib file."
        ) from exc

    return PredictionResult(
        implemented=True,
        outcome=outcome,
        confidence=confidence,
    )


def _load_outcome_model():
    global _model, _model_stamp
    path = _find_outcome_model()
    if path is None:
        return None

    stamp = (path, path.stat().st_mtime_ns)
    if _model is None or _model_stamp != stamp:
        _model = joblib.load(path)
        _model_stamp = stamp
    return _model


def _find_outcome_model():
    files = sorted(path for path in SERVICE_DIR.glob("*.joblib") if path.is_file())
    if not files:
        return None

    preferred = [
        path for path in files
        if "outcome" in path.stem.lower() or "svm" in path.stem.lower()
    ]
    if len(preferred) == 1:
        return preferred[0]
    if len(files) == 1:
        return files[0]

    names = ", ".join(path.name for path in files)
    raise HTTPException(
        status_code=500,
        detail=f"More than one .joblib file is in services ({names}). Leave only the outcome model there."
    )


def _to_outcome(label):
    text = str(label).strip().lower()
    if text in ACCEPTED_LABELS or text.endswith((" allowed", " accepted", " granted")):
        return "Accepted"
    if text in REJECTED_LABELS or text.endswith((" dismissed", " rejected", " denied")):
        return "Rejected"

    raise HTTPException(
        status_code=500,
        detail=f"The outcome model returned '{label}', which is not mapped to Accepted or Rejected."
    )


def _confidence(model, text, label):
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([text])[0]
        classes = list(getattr(model, "classes_", range(len(probabilities))))
        for class_label, probability in zip(classes, probabilities):
            if class_label == label or str(class_label) == str(label):
                return _unit_float(probability)
        return _unit_float(max(probabilities))

    if hasattr(model, "decision_function"):
        score = np.atleast_1d(model.decision_function([text])).reshape(-1)
        margin = abs(float(score[0]))
        return _unit_float(1 / (1 + math.exp(-margin)))

    return None


def _unit_float(value):
    number = float(value)
    if number < 0:
        return 0.0
    if number > 1:
        return 1.0
    return number


def library_case_to_dict(row):
    (
        case_id,
        title,
        citation,
        court,
        decided_year,
        outcome,
        content,
        created_by,
        created_at,
    ) = row

    return {
        "id": str(case_id),
        "title": title,
        "citation": citation,
        "court": court,
        "decided_year": decided_year,
        "outcome": outcome,
        "content": content,
        "created_by": created_by,
        "created_at": created_at.isoformat(),
    }
