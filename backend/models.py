
"""
SpareSync Investigation Model

Defines the structure of an inventory investigation record.
"""

from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Investigation:
    investigation_id: str
    part_id: str
    part_name: Optional[str]
    location: str
    system_stock: int
    physical_stock: int
    variance: int
    root_cause: Optional[str]
    recommended_action: Optional[str]
    confidence: Optional[float]
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Investigation":
        """
        Convert a SQLite database row into an Investigation object.
        """

        return cls(
            investigation_id=row["investigation_id"],
            part_id=row["part_id"],
            part_name=row["part_name"],
            location=row["location"],
            system_stock=row["system_stock"],
            physical_stock=row["physical_stock"],
            variance=row["variance"],
            root_cause=row["root_cause"],
            recommended_action=row["recommended_action"],
            confidence=row["confidence"],
            status=row["status"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
