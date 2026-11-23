
"""
SpareSync Investigation API Routes

Provides REST endpoints for investigation management.
"""

from fastapi import APIRouter, HTTPException, status

from backend.schemas import (
    InvestigationCreate,
    InvestigationUpdate,
    InvestigationResponse
)

from backend.services.investigation_service import (
    create_investigation,
    get_investigation,
    get_all_investigations,
    update_investigation,
    delete_investigation
)


router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"]
)


@router.post(
    "/",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_investigation(data: InvestigationCreate):
    """Create a new investigation."""

    return create_investigation(data)


@router.get(
    "/",
    response_model=list[InvestigationResponse]
)
def list_investigations():
    """Retrieve all investigations."""

    return get_all_investigations()


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse
)
def retrieve_investigation(investigation_id: str):
    """Retrieve an investigation by ID."""

    investigation = get_investigation(investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found."
        )

    return investigation


@router.put(
    "/{investigation_id}",
    response_model=InvestigationResponse
)
def modify_investigation(
    investigation_id: str,
    data: InvestigationUpdate
):
    """Update an existing investigation."""

    investigation = update_investigation(
        investigation_id,
        data
    )

    if investigation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found."
        )

    return investigation


@router.delete("/{investigation_id}")
def remove_investigation(investigation_id: str):
    """Delete an investigation."""

    deleted = delete_investigation(investigation_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation not found."
        )

    return {
        "message": "Investigation deleted successfully.",
        "investigation_id": investigation_id
    }
