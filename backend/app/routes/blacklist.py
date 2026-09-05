"""Blacklist management routes — list, add, and deactivate entries.

All records are demonstration / synthetic data only.
Uses parameterized SQL throughout. No raw personal data is logged.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, field_validator

from app.database.session import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


# ──────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────

class BlacklistRecord(BaseModel):
    """Sanitized blacklist record returned by list/add endpoints."""
    document_number: str
    full_name: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    reason: str
    severity: str
    is_active: bool
    created_at: Optional[str] = None


class BlacklistListResponse(BaseModel):
    """List response for the blacklist endpoint."""
    disclaimer: str
    total: int
    records: List[BlacklistRecord]


class AddBlacklistRequest(BaseModel):
    """Input schema for POST /api/blacklist."""
    document_number: str
    full_name: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    reason: str
    severity: str = "HIGH"

    @field_validator("document_number")
    @classmethod
    def validate_document_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("document_number must not be empty")
        if len(v) > 50:
            raise ValueError("document_number must be 50 characters or fewer")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("reason must not be empty")
        if len(v) > 300:
            raise ValueError("reason must be 300 characters or fewer")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}")
        return v

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v if v else None

    @field_validator("nationality")
    @classmethod
    def sanitize_nationality(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip().upper() or None

    @field_validator("date_of_birth")
    @classmethod
    def sanitize_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip() or None


class AddBlacklistResponse(BaseModel):
    """Response returned after a successful blacklist add."""
    success: bool
    message: str
    record: BlacklistRecord


class DeactivateResponse(BaseModel):
    """Response returned after deactivating a blacklist entry."""
    success: bool
    message: str
    document_number: str


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@router.get(
    "/blacklist",
    response_model=BlacklistListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Blacklist Records",
    description=(
        "Returns blacklist records. Supports optional ?active_only=true (default), "
        "?severity=HIGH, and ?search=<substring> query parameters."
    ),
)
def list_blacklist(
    active_only: bool = Query(True, description="Return only active records"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW / MEDIUM / HIGH / CRITICAL"),
    search: Optional[str] = Query(None, description="Substring match on document_number or full_name"),
) -> BlacklistListResponse:
    """Retrieve blacklist records with optional filters."""
    if severity and severity.upper() not in VALID_SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid severity filter. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}",
        )

    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            conditions = []
            params: List = []

            if active_only:
                conditions.append("is_active = 1")
            if severity:
                conditions.append("severity = ?")
                params.append(severity.upper())
            if search:
                conditions.append(
                    "(UPPER(document_number) LIKE ? OR UPPER(COALESCE(full_name, '')) LIKE ?)"
                )
                term = f"%{search.strip().upper()}%"
                params.extend([term, term])

            where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
            cursor.execute(
                f"""
                SELECT document_number, full_name, nationality, date_of_birth,
                       reason, severity, is_active, created_at
                FROM blacklist
                {where_clause}
                ORDER BY id DESC;
                """,
                params,
            )
            rows = cursor.fetchall()
            records = [
                BlacklistRecord(
                    document_number=row["document_number"],
                    full_name=row["full_name"],
                    nationality=row["nationality"],
                    date_of_birth=row["date_of_birth"],
                    reason=row["reason"],
                    severity=row["severity"],
                    is_active=bool(row["is_active"]),
                    created_at=row["created_at"],
                )
                for row in rows
            ]
            return BlacklistListResponse(
                disclaimer="DEVELOPMENT / DEMONSTRATION BLACKLIST ONLY — ALL RECORDS ARE SYNTHETIC",
                total=len(records),
                records=records,
            )
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error listing blacklist records", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to query blacklist database.",
        )


@router.post(
    "/blacklist",
    response_model=AddBlacklistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Entry to Blacklist",
    description="Adds a new synthetic demonstration entry to the blacklist. Prevents duplicate active records.",
)
def add_blacklist_entry(body: AddBlacklistRequest) -> AddBlacklistResponse:
    """Add a new entry to the demonstration blacklist."""
    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # Check for existing active record with the same document_number
            cursor.execute(
                "SELECT id, is_active FROM blacklist WHERE UPPER(document_number) = ? LIMIT 1;",
                (body.document_number,),
            )
            existing = cursor.fetchone()

            if existing is not None:
                if bool(existing["is_active"]):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Document is already active in the blacklist. Deactivate the existing record first.",
                    )
                else:
                    # Reactivate the deactivated record with updated fields
                    cursor.execute(
                        """
                        UPDATE blacklist
                        SET full_name = ?,
                            nationality = ?,
                            date_of_birth = ?,
                            reason = ?,
                            severity = ?,
                            is_active = 1,
                            created_at = datetime('now')
                        WHERE UPPER(document_number) = ?;
                        """,
                        (
                            body.full_name,
                            body.nationality,
                            body.date_of_birth,
                            body.reason,
                            body.severity,
                            body.document_number,
                        ),
                    )
                    conn.commit()
                    message = "Previously deactivated record reactivated in blacklist"
            else:
                # Insert new record
                cursor.execute(
                    """
                    INSERT INTO blacklist (document_number, full_name, nationality, date_of_birth, reason, severity, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1);
                    """,
                    (
                        body.document_number,
                        body.full_name,
                        body.nationality,
                        body.date_of_birth,
                        body.reason,
                        body.severity,
                    ),
                )
                conn.commit()
                message = "Document successfully added to blacklist"

            # Fetch the final record
            cursor.execute(
                """
                SELECT document_number, full_name, nationality, date_of_birth,
                       reason, severity, is_active, created_at
                FROM blacklist
                WHERE UPPER(document_number) = ?;
                """,
                (body.document_number,),
            )
            row = cursor.fetchone()
            record = BlacklistRecord(
                document_number=row["document_number"],
                full_name=row["full_name"],
                nationality=row["nationality"],
                date_of_birth=row["date_of_birth"],
                reason=row["reason"],
                severity=row["severity"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )
            return AddBlacklistResponse(success=True, message=message, record=record)

        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error adding blacklist entry", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to add entry to blacklist database.",
        )


@router.patch(
    "/blacklist/{document_number}/deactivate",
    response_model=DeactivateResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a Blacklist Entry",
    description="Sets is_active=0 for the given document_number. Preserves the row for audit purposes.",
)
def deactivate_blacklist_entry(document_number: str) -> DeactivateResponse:
    """Deactivate a blacklist record without deleting it."""
    clean_doc = document_number.strip().upper()
    if not clean_doc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="document_number must not be empty.",
        )

    try:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, is_active FROM blacklist WHERE UPPER(document_number) = ? LIMIT 1;",
                (clean_doc,),
            )
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No blacklist record found for document number: {clean_doc}",
                )
            if not bool(row["is_active"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Record is already inactive.",
                )
            cursor.execute(
                "UPDATE blacklist SET is_active = 0 WHERE UPPER(document_number) = ?;",
                (clean_doc,),
            )
            conn.commit()
            return DeactivateResponse(
                success=True,
                message=f"Blacklist record for {clean_doc} has been deactivated.",
                document_number=clean_doc,
            )
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception:
        logger.error("Error deactivating blacklist entry", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to deactivate blacklist record.",
        )
