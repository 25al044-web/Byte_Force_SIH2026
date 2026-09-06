"""Case management and review endpoints for SIH26188."""

from fastapi import APIRouter, HTTPException, Query
from app.services.case_service import list_cases, get_case

router = APIRouter()


@router.get("/cases")
def get_cases(all_cases: bool = Query(default=False, description="Include all cases regardless of risk level")):
    """List screening cases requiring officer review."""
    cases = list_cases(only_requiring_review=not all_cases)
    return {
        "cases": cases,
        "total": len(cases),
    }


@router.get("/cases/{screening_id}")
def get_single_case(screening_id: str):
    """Retrieve details for a single screening case."""
    case = get_case(screening_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{screening_id}' not found.")
    return case
