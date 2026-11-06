"""
Precedent Recommender Engine for Nyaay Sakha.
Searches 36,000 pre-indexed High Court precedents using TF-IDF + Cosine Similarity.
"""

import math
from pathlib import Path
import re
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas.analysis import SimilarCase, SimilarCasesResult

SERVICE_DIR = Path(__file__).resolve().parent
FALLBACK_DIR = Path(r"C:\Users\Ayush Anand\Desktop\ppp\models")

_recommender = None
_vectorizer = None
_cnr_cache = None


def _find_file(filename):
    local = SERVICE_DIR / filename
    if local.is_file():
        return local
    fallback = FALLBACK_DIR / filename
    if fallback.is_file():
        return fallback
    return None


def load_recommender():
    global _recommender, _vectorizer
    if _recommender is None:
        rec_path = _find_file("case_recommender.joblib")
        if rec_path is not None:
            _recommender = joblib.load(rec_path)
    if _vectorizer is None:
        vec_path = _find_file("tfidf_vectorizer.joblib")
        if vec_path is not None:
            _vectorizer = joblib.load(vec_path)
        elif _recommender is not None:
            pipe_path = _find_file("lightgbm_outcome.joblib")
            if pipe_path is not None:
                pipe = joblib.load(pipe_path)
                if hasattr(pipe, "named_steps") and "tfidf" in pipe.named_steps:
                    _vectorizer = pipe.named_steps["tfidf"]
    return _recommender, _vectorizer


def _clean_snippet(snippet_text, max_chars=350):
    if not snippet_text:
        return None
    cleaned = re.sub(r"^CASE_TYPE_\w+\s+", "", str(snippet_text)).strip()
    compact = " ".join(cleaned.split())
    if len(compact) > max_chars:
        return compact[:max_chars].rstrip() + "..."
    return compact


def _map_outcome_and_label(raw_outcome):
    from app.services.legal_models import _format_detailed_label, _to_outcome
    detailed = _format_detailed_label(raw_outcome) if raw_outcome else None
    try:
        primary = _to_outcome(raw_outcome) if raw_outcome else "Accepted"
    except Exception:
        primary = "Accepted"
    return primary, detailed


def get_precedent_recommendations(query_text, user_library=None, top_k=5):
    query = str(query_text or "").strip()
    if not query:
        return SimilarCasesResult(implemented=True, requested=top_k, cases=[])

    rec, vec = load_recommender()

    # Fallback to ad-hoc search across user_library if corpus recommender is absent
    if rec is None or vec is None:
        return _fallback_user_search(query, user_library, top_k)

    corpus_mat = rec.get("corpus_matrix")
    metadata = rec.get("metadata", [])
    total_cases = len(metadata)

    # 1. Vectorize query
    q_vec = vec.transform([query])

    # 2. Compute similarity with corpus (36,000 cases)
    scores = corpus_mat.dot(q_vec.T).toarray().ravel()
    top_indices = np.argsort(scores)[-top_k:][::-1]

    candidates = []
    for idx in top_indices:
        score = float(scores[idx])
        if score <= 0.0:
            continue
        m = metadata[idx] if idx < len(metadata) else {}
        raw_out = m.get("outcome") or m.get("raw_disposal")
        primary_outcome, detailed_label = _map_outcome_and_label(raw_out)

        year = None
        if m.get("year") and str(m["year"]).isdigit():
            year = int(m["year"])

        candidates.append({
            "score": score,
            "case_id": m.get("cnr") or f"corpus-{idx}",
            "title": m.get("title") or "High Court Precedent",
            "citation": m.get("case_type") or m.get("cnr"),
            "court": "Patna High Court",
            "decided_year": year,
            "outcome": primary_outcome,
            "detailed_label": detailed_label,
            "judge": m.get("judge") or None,
            "snippet": _clean_snippet(m.get("factual_snippet") or m.get("clean_full_text")),
            "full_text": m.get("clean_full_text") or m.get("full_context") or m.get("factual_snippet"),
        })

    # 3. Check user library if available and merge
    if user_library:
        user_cases = [c for c in user_library if str(c.get("content") or "").strip()]
        if user_cases:
            user_mat = vec.transform([c["content"] for c in user_cases])
            u_scores = user_mat.dot(q_vec.T).toarray().ravel()
            for c, u_score in zip(user_cases, u_scores):
                if float(u_score) > 0.0:
                    primary_out, detailed_lbl = _map_outcome_and_label(c.get("outcome"))
                    candidates.append({
                        "score": float(u_score),
                        "case_id": str(c.get("id")),
                        "title": c.get("title") or "User Precedent",
                        "citation": c.get("citation"),
                        "court": c.get("court") or "User Precedent Library",
                        "decided_year": c.get("decided_year"),
                        "outcome": primary_out,
                        "detailed_label": detailed_lbl,
                        "judge": None,
                        "snippet": _clean_snippet(c.get("content")),
                        "full_text": c.get("content"),
                    })

    # 4. Sort all candidates descending by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = candidates[:top_k]

    cases = [
        SimilarCase(
            rank=rank,
            case_id=c["case_id"],
            title=c["title"],
            citation=c["citation"],
            court=c["court"],
            decided_year=c["decided_year"],
            outcome=c["outcome"],
            detailed_label=c["detailed_label"],
            judge=c["judge"],
            snippet=c["snippet"],
            full_text=c["full_text"],
            similarity=round(c["score"], 4),
        )
        for rank, c in enumerate(selected, start=1)
    ]

    return SimilarCasesResult(
        method="tfidf_cosine",
        implemented=True,
        requested=top_k,
        total_corpus_cases=total_cases,
        cases=cases,
    )


def get_precedent_by_id(case_id: str):
    """Retrieve full judgment details for a specific case by its CNR or identifier."""
    global _cnr_cache
    rec, _ = load_recommender()
    if not rec:
        return None

    metadata = rec.get("metadata", [])
    if _cnr_cache is None:
        _cnr_cache = {
            m.get("cnr"): m
            for m in metadata
            if m.get("cnr")
        }

    m = _cnr_cache.get(case_id)
    if not m and case_id.startswith("corpus-"):
        idx_str = case_id.replace("corpus-", "")
        if idx_str.isdigit():
            idx = int(idx_str)
            if 0 <= idx < len(metadata):
                m = metadata[idx]

    if not m:
        return None

    raw_out = m.get("outcome") or m.get("raw_disposal")
    primary_outcome, detailed_label = _map_outcome_and_label(raw_out)
    year = int(m["year"]) if m.get("year") and str(m["year"]).isdigit() else None

    return {
        "case_id": m.get("cnr"),
        "title": m.get("title") or "High Court Precedent",
        "citation": m.get("case_type") or m.get("cnr"),
        "court": "Patna High Court",
        "decision_date": m.get("decision_date"),
        "decided_year": year,
        "judge": m.get("judge"),
        "outcome": primary_outcome,
        "detailed_label": detailed_label,
        "snippet": _clean_snippet(m.get("factual_snippet") or m.get("clean_full_text")),
        "full_text": m.get("clean_full_text") or m.get("full_context") or m.get("factual_snippet"),
    }


def _fallback_user_search(query, user_library, top_k):
    candidates = [
        case for case in (user_library or [])
        if str(case.get("content") or "").strip()
    ]
    if not candidates:
        return SimilarCasesResult(implemented=True, requested=top_k, cases=[])

    matrix = TfidfVectorizer(
        stop_words="english",
        max_features=20000,
    ).fit_transform([query, *(case["content"] for case in candidates)])
    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    ranked = sorted(
        ((float(score), case) for score, case in zip(scores, candidates) if score > 0),
        key=lambda item: item[0],
        reverse=True,
    )

    cases = [
        SimilarCase(
            rank=rank,
            case_id=str(case["id"]),
            title=case["title"],
            citation=case.get("citation"),
            court=case.get("court") or "User Library",
            decided_year=case.get("decided_year"),
            outcome=case.get("outcome"),
            detailed_label=None,
            judge=None,
            snippet=_clean_snippet(case.get("content")),
            full_text=case.get("content"),
            similarity=round(float(score), 4),
        )
        for rank, (score, case) in enumerate(ranked[:top_k], start=1)
    ]

    return SimilarCasesResult(
        method="tfidf_cosine",
        implemented=True,
        requested=top_k,
        total_corpus_cases=len(candidates),
        cases=cases,
    )
