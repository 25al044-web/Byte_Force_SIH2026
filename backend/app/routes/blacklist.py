"""Development endpoint for demonstration blacklist inspection."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from app.database.session import get_db_connection

router = APIRouter()


class BlacklistDemoRecord(BaseModel):
    """Sanitized blacklist record for demonstration purposes."""
    document_number: str
    full_name: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    reason: str
    severity: str
    is_active: bool


class BlacklistListResponse(BaseModel):
    """List response for the development blacklist endpoint."""
    disclaimer: str
    total: int
    records: List[BlacklistDemoRecord]


@router.get(
    "/blacklist",
    response_model=BlacklistListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Demonstration Blacklist Records (DEVELOPMENT ONLY)",
    description=(
        "Returns sanitized synthetic blacklist demonstration entries for debugging "
        "and demonstration. Does NOT contain real personal data."
    ),
)
def list_demonstration_blacklist() -> BlacklistListResponse:
    """Retrieve synthetic demonstration blacklist records."""
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT document_number, full_name, nationality, date_of_birth, reason, severity, is_active
                FROM blacklist
                ORDER BY id ASC;
                """
            )
            rows = cursor.fetchall()
            records = [
                BlacklistDemoRecord(
                    document_number=row["document_number"],
                    full_name=row["full_name"],
                    nationality=row["nationality"],
                    date_of_birth=row["date_of_birth"],
                    reason=row["reason"],
                    severity=row["severity"],
                    is_active=bool(row["is_active"]),
                )
                for row in rows
            ]
            return BlacklistListResponse(
                disclaimer="DEVELOPMENT / DEMONSTRATION BLACKLIST ONLY - ALL RECORDS ARE SYNTHETIC",
                total=len(records),
                records=records,
            )
        finally:
            conn.close()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to query demonstration blacklist database: {str(exc)}",
        )
