"""
Hooks for the three legal-document models.

These functions define the inputs and outputs the routes already use.
LexRank, TF-IDF cosine similarity, and the SVM classifier are not
implemented here.
"""

from app.schemas.analysis import (
    PredictionResult,
    SimilarCasesResult,
    SummaryResult,
)


def lexrank_summarize(text):
    return SummaryResult()


def recommend_similar_cases(text, library, top_k=5):
    return SimilarCasesResult(
        requested=top_k,
        cases=[]
    )


def predict_outcome(text):
    return PredictionResult()


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
