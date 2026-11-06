from typing import Literal

from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    method: str = "enhanced_lexrank"
    implemented: bool = False
    summary: str | None = None
    sentences: list[str] = []
    key_points: list[str] = []
    reduction_pct: int | None = None
    word_count: int | None = None


class SimilarCase(BaseModel):
    rank: int
    case_id: str | None = None
    title: str | None = None
    citation: str | None = None
    court: str | None = None
    decided_year: int | None = None
    outcome: Literal["Accepted", "Rejected", "Disposed"] | str | None = None
    detailed_label: str | None = None
    judge: str | None = None
    snippet: str | None = None
    full_text: str | None = None
    similarity: float | None = None


class SimilarCasesResult(BaseModel):
    method: str = "tfidf_cosine"
    implemented: bool = False
    requested: int = 5
    total_corpus_cases: int | None = None
    cases: list[SimilarCase] = []


class PredictionResult(BaseModel):
    method: str = "lightgbm"
    implemented: bool = False
    outcome: Literal["Accepted", "Rejected", "Disposed"] | str | None = None
    detailed_label: str | None = None
    confidence: float | None = None
    probabilities: dict[str, float] | None = None
    detail: str | None = None


class UploadRecord(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    characters: int
    excerpt: str
    created_at: str


class AnalyzeResponse(BaseModel):
    filename: str
    characters: int
    excerpt: str
    upload: UploadRecord
    summary: SummaryResult
    similar_cases: SimilarCasesResult
    prediction: PredictionResult
    disclaimer: str


class SummaryResponse(BaseModel):
    filename: str
    characters: int
    excerpt: str
    upload: UploadRecord
    summary: SummaryResult
    disclaimer: str


class SimilarCasesResponse(BaseModel):
    filename: str
    characters: int
    excerpt: str
    upload: UploadRecord
    similar_cases: SimilarCasesResult
    disclaimer: str


class PredictionResponse(BaseModel):
    filename: str
    characters: int
    excerpt: str
    upload: UploadRecord
    prediction: PredictionResult
    disclaimer: str


class LibraryCaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1)
    outcome: Literal["Accepted", "Rejected"]
    citation: str | None = Field(default=None, max_length=300)
    court: str | None = Field(default=None, max_length=200)
    decided_year: int | None = Field(default=None, ge=1800, le=2100)


class LibraryCase(BaseModel):
    id: str
    title: str
    citation: str | None = None
    court: str | None = None
    decided_year: int | None = None
    outcome: Literal["Accepted", "Rejected"]
    content: str | None = None
    created_by: str
    created_at: str
