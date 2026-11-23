
"""
SpareSync Investigation Service

Handles investigation CRUD operations using SQLite.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from backend.database import get_db_connection
from backend.models import Investigation
from backend.schemas import InvestigationCreate, InvestigationUpdate


def create_investigation(
    investigation_data: InvestigationCreate
) -> Investigation:

    """Create and store a new investigation."""

    investigation_id = f"INV-{uuid.uuid4().hex[:10].upper()}"
    current_time = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO investigations (
                investigation_id,
                part_id,
                part_name,
                location,
                system_stock,
                physical_stock,
                variance,
                root_cause,
                recommended_action,
                confidence,
                status,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                investigation_id,
                investigation_data.part_id,
                investigation_data.part_name,
                investigation_data.location,
                investigation_data.system_stock,
                investigation_data.physical_stock,
                investigation_data.variance,
                investigation_data.root_cause,
                investigation_data.recommended_action,
                investigation_data.confidence,
                "OPEN",
                investigation_data.notes,
                current_time,
                current_time
            )
        )

        row = connection.execute(
            """
            SELECT * FROM investigations
            WHERE investigation_id = ?
            """,
            (investigation_id,)
        ).fetchone()

    return Investigation.from_row(row)


def get_investigation(
    investigation_id: str
) -> Optional[Investigation]:

    """Retrieve one investigation by its ID."""

    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM investigations
            WHERE investigation_id = ?
            """,
            (investigation_id,)
        ).fetchone()

    if row is None:
        return None

    return Investigation.from_row(row)


def get_all_investigations() -> list[Investigation]:

    """Retrieve all investigations, newest first."""

    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM investigations
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        Investigation.from_row(row)
        for row in rows
    ]


def update_investigation(
    investigation_id: str,
    update_data: InvestigationUpdate
) -> Optional[Investigation]:

    """Update an existing investigation."""

    updates = update_data.model_dump(exclude_unset=True)

    if not updates:
        return get_investigation(investigation_id)

    allowed_fields = {
        "root_cause",
        "recommended_action",
        "confidence",
        "status",
        "notes"
    }

    if not set(updates).issubset(allowed_fields):
        raise ValueError("Invalid investigation update fields.")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    set_clause = ", ".join(
        f"{field} = ?" for field in updates
    )

    values = list(updates.values())
    values.append(investigation_id)

    with get_db_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE investigations
            SET {set_clause}
            WHERE investigation_id = ?
            """,
            values
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            """
            SELECT * FROM investigations
            WHERE investigation_id = ?
            """,
            (investigation_id,)
        ).fetchone()

    return Investigation.from_row(row)


def delete_investigation(
    investigation_id: str
) -> bool:

    """Delete an investigation by its ID."""

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM investigations
            WHERE investigation_id = ?
            """,
            (investigation_id,)
        )

        return cursor.rowcount > 0
