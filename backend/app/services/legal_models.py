"""
Hooks for the three legal-document models.

Summaries use the LexRank implementation in lexRank.py.
TF-IDF cosine similarity and the SVM classifier are not implemented here.
"""

from app.schemas.analysis import (
    PredictionResult,
    SimilarCasesResult,
    SummaryResult,
)
from app.services.lexRank import lexrank_summarize as run_lexrank

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
