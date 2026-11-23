
"""
SpareSync API Schemas

Defines request and response validation using Pydantic.
"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict, model_validator


InvestigationStatus = Literal[
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
    "ESCALATED"
]


class InvestigationCreate(BaseModel):
    """Schema for creating a new investigation."""

    part_id: str = Field(min_length=1, max_length=50)
    part_name: Optional[str] = Field(default=None, max_length=150)
    location: str = Field(min_length=1, max_length=150)

    system_stock: int = Field(ge=0)
    physical_stock: int = Field(ge=0)

    root_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def calculate_variance(self):
        """Calculate variance from stock values."""

        self.variance = self.system_stock - self.physical_stock
        return self

    variance: int = 0


class InvestigationUpdate(BaseModel):
    """Schema for updating an investigation."""

    root_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    status: Optional[InvestigationStatus] = None
    notes: Optional[str] = None


class InvestigationResponse(BaseModel):
    """Schema returned by investigation API endpoints."""

    model_config = ConfigDict(from_attributes=True)

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

    created_at: datetime
    updated_at: datetime
