from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import get_current_user
from app.db.library import load_precedents
from app.schemas.analysis import (
    AnalyzeResponse,
    PredictionResponse,
    SimilarCasesResponse,
    SummaryResponse,
)
from app.services.case_uploads import store_uploaded_case
from app.services.documents import DISCLAIMER
from app.services.legal_models import (
    lexrank_summarize,
    library_case_to_dict,
    predict_outcome,
    recommend_similar_cases,
)

router = APIRouter(prefix="/analysis", tags=["Case Analysis"])
TOP_SIMILAR_CASES = 5


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_case(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    text, upload = await store_uploaded_case(file, user["user_id"])

    return AnalyzeResponse(
        **_document_fields(upload),
        summary=lexrank_summarize(text),
        similar_cases=recommend_similar_cases(
            text,
            _precedent_library(),
            top_k=TOP_SIMILAR_CASES,
        ),
        prediction=predict_outcome(text),
    )


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_case(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    text, upload = await store_uploaded_case(file, user["user_id"])

    return SummaryResponse(
        **_document_fields(upload),
        summary=lexrank_summarize(text),
    )


@router.post("/similar-cases", response_model=SimilarCasesResponse)
async def similar_cases(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    text, upload = await store_uploaded_case(file, user["user_id"])

    return SimilarCasesResponse(
        **_document_fields(upload),
        similar_cases=recommend_similar_cases(
            text,
            _precedent_library(),
            top_k=TOP_SIMILAR_CASES,
        ),
    )


@router.post("/predict", response_model=PredictionResponse)
async def predict_case(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    text, upload = await store_uploaded_case(file, user["user_id"])

    return PredictionResponse(
        **_document_fields(upload),
        prediction=predict_outcome(text),
    )


def _document_fields(upload):
    return {
        "filename": upload["filename"],
        "characters": upload["characters"],
        "excerpt": upload["excerpt"],
        "upload": upload,
        "disclaimer": DISCLAIMER,
    }


def _precedent_library():
    try:
        rows = load_precedents()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Case library is unavailable"
        )

    return [library_case_to_dict(row) for row in rows]
