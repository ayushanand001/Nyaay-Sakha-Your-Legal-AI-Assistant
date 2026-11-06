"""
Hooks for the three legal-document models.

Summaries use the LexRank implementation in lexRank.py.
Outcome prediction loads the .joblib classifier placed in this folder.
Similar precedents use the 36,000 High Court case recommender engine.
"""

import math
from pathlib import Path

import joblib
import numpy as np
from fastapi import HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas.analysis import (
    PredictionResult,
    SimilarCasesResult,
    SummaryResult,
)
from app.services.lexRank import enhanced_lexrank_summarize
from app.services.preprocess import prepare_case_text

SERVICE_DIR = Path(__file__).resolve().parent
ACCEPTED_LABELS = {
    "1",
    "accepted",
    "accept",
    "allowed",
    "allow",
    "granted",
    "grant",
    "bail_granted",
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
    "bail_rejected",
    "no",
    "false",
    "negative",
}
DISPOSED_LABELS = {
    "disposed",
    "dispose",
    "disposed_other",
}
_model = None
_model_stamp = None

SUMMARY_SENTENCES = 5


def lexrank_summarize(text):
    res = enhanced_lexrank_summarize(text, num_sentences=SUMMARY_SENTENCES)

    return SummaryResult(
        method="enhanced_lexrank",
        implemented=True,
        summary=res.get("summary"),
        sentences=res.get("sentences", []),
        key_points=res.get("key_points", []),
        reduction_pct=res.get("reduction_pct"),
        word_count=res.get("word_count"),
    )


def recommend_similar_cases(text, library, top_k=5):
    from app.services.recommender import get_precedent_recommendations
    return get_precedent_recommendations(text, user_library=library, top_k=top_k)


def _get_model_method_name(model):
    if hasattr(model, "named_steps"):
        clf = model.named_steps.get("classifier") or list(model.named_steps.values())[-1]
        name = clf.__class__.__name__.lower()
        if "lgbm" in name or "lightgbm" in name:
            return "lightgbm"
        if "svm" in name or "svc" in name:
            return "svm"
        if "logistic" in name:
            return "logistic_regression"
        return name
    return "lightgbm"


def _format_detailed_label(label):
    raw = str(label).strip().lower()
    mapping = {
        "allowed": "Allowed",
        "bail_granted": "Bail Granted",
        "bail_rejected": "Bail Rejected",
        "dismissed": "Dismissed",
        "disposed": "Disposed",
        "disposed_other": "Disposed",
    }
    return mapping.get(raw, raw.replace("_", " ").title())


def _get_probabilities(model, text):
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba([text])[0]
        classes = list(getattr(model, "classes_", range(len(probs))))
        return {
            _format_detailed_label(cls_name): round(float(prob), 4)
            for cls_name, prob in zip(classes, probs)
        }
    return None


def predict_outcome(text):
    model = _load_outcome_model()
    if model is None:
        return PredictionResult()

    model_text, status = prepare_case_text(text)
    if not model_text:
        return PredictionResult(
            implemented=True,
            detail=_preparation_detail(status),
        )

    try:
        label = model.predict([model_text])[0]
        outcome = _to_outcome(label)
        detailed_label = _format_detailed_label(label)
        confidence = _confidence(model, model_text, label)
        probabilities = _get_probabilities(model, model_text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The outcome model could not score this document. It needs to accept the case text directly, usually as a scikit-learn pipeline saved in one .joblib file."
        ) from exc

    return PredictionResult(
        method=_get_model_method_name(model),
        implemented=True,
        outcome=outcome,
        detailed_label=detailed_label,
        confidence=confidence,
        probabilities=probabilities,
    )


def _preparation_detail(status):
    if status in ("document_too_short", "analysis_removal_too_short"):
        return (
            "The document is shorter than 500 characters, so it could not be scored."
        )
    return (
        "The case text could not be prepared for scoring."
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
    files = sorted(
        path for path in SERVICE_DIR.glob("*.joblib")
        if path.is_file() and not any(k in path.stem.lower() for k in ("recommender", "vectorizer"))
    )
    if not files:
        return None

    preferred = [
        path for path in files
        if any(keyword in path.stem.lower() for keyword in ("lightgbm", "lgbm", "outcome", "svm"))
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
    if (
        text in ACCEPTED_LABELS
        or text.endswith((" allowed", " accepted", " granted", "_allowed", "_accepted", "_granted"))
    ):
        return "Accepted"
    if (
        text in REJECTED_LABELS
        or text.endswith((" dismissed", " rejected", " denied", "_dismissed", "_rejected", "_denied"))
    ):
        return "Rejected"
    if text in DISPOSED_LABELS or "disposed" in text:
        # In legal classification, 'disposed' represents a non-dismissed resolution
        return "Accepted"

    raise HTTPException(
        status_code=500,
        detail=f"The outcome model returned '{label}', which is not mapped to Accepted, Rejected, or Disposed."
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
