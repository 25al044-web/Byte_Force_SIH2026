"""Trusted Identity Registry API routes.

Provides endpoints to list, create, view, update, deactivate, and lookup
verified identities in the local demo Trusted Identity Registry.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.services.trusted_registry import (
    deactivate_trusted_identity,
    get_trusted_identity,
    list_trusted_identities,
    lookup_trusted_identity,
    register_trusted_identity,
    update_trusted_identity,
)

logger = logging.getLogger(__name__)

router = APIRouter()

REGISTRY_DISCLAIMER = (
    "Authoritative local demonstration trusted identity registry. "
    "Maintained for simulated border cross-verification testing; "
    "no external government databases are contacted."
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TrustedIdentitySchema(BaseModel):
    id: Optional[int] = None
    registry_id: str
    full_name: str
    document_number: str
    document_type: str
    date_of_birth: str
    nationality: Optional[str] = None
    has_reference_photo: bool = False
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TrustedIdentityListResponse(BaseModel):
    disclaimer: str
    total: int
    records: List[TrustedIdentitySchema]


class CreateTrustedIdentityJsonRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    document_number: str = Field(..., min_length=1, max_length=50)
    document_type: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., min_length=1, max_length=30)
    nationality: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=500)
    registry_id: Optional[str] = Field(None, max_length=50)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/registry", response_model=TrustedIdentityListResponse)
@router.get("/trusted-identities", response_model=TrustedIdentityListResponse)
def get_trusted_identities(
    search: Optional[str] = Query(None, description="Search by name, document number, or registry ID"),
    active_only: bool = Query(False, description="Filter only active records"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List trusted identity records in the local demonstration registry."""
    records = list_trusted_identities(
        search=search,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return {
        "disclaimer": REGISTRY_DISCLAIMER,
        "total": len(records),
        "records": records,
    }


@router.post("/registry", status_code=status.HTTP_201_CREATED)
@router.post("/trusted-identities", status_code=status.HTTP_201_CREATED)
async def create_trusted_identity(request: Request):
    """Register a new identity in the trusted registry.

    Supports both JSON payload and multipart/form-data with photo upload.
    """
    content_type = request.headers.get("content-type", "")

    full_name = ""
    document_number = ""
    document_type = ""
    date_of_birth = ""
    nationality = None
    notes = None
    registry_id = None
    photo_bytes = None
    photo_mime = "image/jpeg"

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}")

        full_name = body.get("full_name", "")
        document_number = body.get("document_number", "")
        document_type = body.get("document_type", "")
        date_of_birth = body.get("date_of_birth", "")
        nationality = body.get("nationality")
        notes = body.get("notes")
        registry_id = body.get("registry_id")
    else:
        # Assume multipart/form-data or form-urlencoded
        try:
            form = await request.form()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid form data: {exc}")

        full_name = str(form.get("full_name") or "")
        document_number = str(form.get("document_number") or "")
        document_type = str(form.get("document_type") or "")
        date_of_birth = str(form.get("date_of_birth") or "")
        nationality = str(form.get("nationality")) if form.get("nationality") else None
        notes = str(form.get("notes")) if form.get("notes") else None
        registry_id = str(form.get("registry_id")) if form.get("registry_id") else None

        photo_field = form.get("photo")
        if photo_field and hasattr(photo_field, "file"):
            photo_bytes = await photo_field.read()
            photo_mime = photo_field.content_type or "image/jpeg"

    if not full_name.strip():
        raise HTTPException(status_code=422, detail="Full name is required")
    if not document_number.strip():
        raise HTTPException(status_code=422, detail="Document number is required")
    if not document_type.strip():
        raise HTTPException(status_code=422, detail="Document type is required")
    if not date_of_birth.strip():
        raise HTTPException(status_code=422, detail="Date of birth is required")

    try:
        created = register_trusted_identity(
            full_name=full_name,
            document_number=document_number,
            document_type=document_type,
            date_of_birth=date_of_birth,
            nationality=nationality,
            notes=notes,
            photo_bytes=photo_bytes,
            photo_mime_type=photo_mime,
            registry_id=registry_id,
        )
        return {
            "disclaimer": REGISTRY_DISCLAIMER,
            "record": created,
        }
    except Exception as exc:
        logger.error("Error registering trusted identity: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/registry/lookup/{document_number}")
@router.get("/trusted-identities/lookup/{document_number}")
def lookup_identity_by_doc(document_number: str):
    """Lookup an active record by document number."""
    rec = lookup_trusted_identity(document_number)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active trusted identity found for document {document_number}",
        )
    # Never return raw photo embedding to client
    rec_copy = dict(rec)
    rec_copy.pop("photo_embedding", None)
    return {
        "disclaimer": REGISTRY_DISCLAIMER,
        "record": rec_copy,
    }


@router.get("/registry/{registry_id}")
@router.get("/trusted-identities/{registry_id}")
def get_single_trusted_identity(registry_id: str):
    """Retrieve details for a single trusted identity."""
    rec = get_trusted_identity(registry_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trusted identity '{registry_id}' not found",
        )
    return {
        "disclaimer": REGISTRY_DISCLAIMER,
        "record": rec,
    }


@router.put("/registry/{registry_id}")
@router.put("/trusted-identities/{registry_id}")
async def update_identity(registry_id: str, request: Request):
    """Update fields or photo of an existing trusted identity."""
    existing = get_trusted_identity(registry_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trusted identity '{registry_id}' not found",
        )

    content_type = request.headers.get("content-type", "")
    updates: Dict[str, Any] = {}
    photo_bytes = None
    photo_mime = "image/jpeg"

    if "application/json" in content_type:
        try:
            updates = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}")
    else:
        try:
            form = await request.form()
            for key, val in form.items():
                if key != "photo":
                    updates[key] = str(val)
            photo_field = form.get("photo")
            if photo_field and hasattr(photo_field, "file"):
                photo_bytes = await photo_field.read()
                photo_mime = photo_field.content_type or "image/jpeg"
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid form data: {exc}")

    updated = update_trusted_identity(
        registry_id=registry_id,
        updates=updates,
        photo_bytes=photo_bytes,
        photo_mime_type=photo_mime,
    )
    return {
        "disclaimer": REGISTRY_DISCLAIMER,
        "record": updated,
    }


@router.post("/registry/{registry_id}/deactivate")
@router.patch("/registry/{registry_id}/deactivate")
@router.post("/trusted-identities/{registry_id}/deactivate")
@router.patch("/trusted-identities/{registry_id}/deactivate")
def deactivate_identity(registry_id: str):
    """Soft-deactivate a trusted identity."""
    success = deactivate_trusted_identity(registry_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trusted identity '{registry_id}' not found or already inactive",
        )
    return {
        "status": "DEACTIVATED",
        "registry_id": registry_id,
        "is_active": False,
        "message": "Trusted identity record successfully deactivated",
    }
