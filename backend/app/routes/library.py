from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user
from app.db.library import delete_case, get_case, insert_case, list_cases
from app.schemas.analysis import LibraryCase, LibraryCaseCreate
from app.services.legal_models import library_case_to_dict

router = APIRouter(prefix="/library", tags=["Precedent Library"])


@router.post("/cases", response_model=LibraryCase, status_code=201)
def add_case(
    data: LibraryCaseCreate,
    user=Depends(get_current_user),
):
    try:
        row = insert_case(user["user_id"], data)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Case library is unavailable"
        )

    return library_case_to_dict(row)


@router.get("/cases", response_model=list[LibraryCase])
def get_cases(
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(get_current_user),
):
    try:
        rows = list_cases(user["user_id"], limit)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Case library is unavailable"
        )

    return [library_case_to_dict(row) for row in rows]


@router.get("/cases/{case_id}", response_model=LibraryCase)
def get_one_case(
    case_id: str,
    user=Depends(get_current_user),
):
    try:
        row = get_case(case_id, user["user_id"])
    except Exception as exc:
        _raise_library_error(exc)

    if not row:
        raise HTTPException(status_code=404, detail="Case not found")

    return library_case_to_dict(row)


@router.delete("/cases/{case_id}")
def remove_case(
    case_id: str,
    user=Depends(get_current_user),
):
    try:
        row = delete_case(case_id, user["user_id"])
    except Exception as exc:
        _raise_library_error(exc)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return {"message": "Case removed"}


def _raise_library_error(exc):
    if "invalid input syntax for type uuid" in str(exc).lower():
        raise HTTPException(status_code=400, detail="Invalid case id")

    raise HTTPException(
        status_code=503,
        detail="Case library is unavailable"
    )
