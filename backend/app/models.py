"""Models for the PearlCard fare calculation system."""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import IntEnum


class Journey(BaseModel):
    """Model representing a single journey."""
    from_zone: int = Field(..., ge=1, description="Starting zone")
    to_zone: int = Field(..., ge=1, description="Ending zone")
    
    @validator('from_zone', 'to_zone')
    def validate_zone(cls, v):
        # Dynamic zone validation - will check against database
        from app.config import settings
        if not settings.is_valid_zone(v):
            raise ValueError(f"Zone {v} is not valid. Check available zones from API.")
        return v


class JourneyWithFare(Journey):
    """Journey model extended with calculated fare."""
    fare: float = Field(..., description="Calculated fare for this journey")
    journey_id: Optional[int] = Field(None, description="Unique journey identifier")


class JourneyRequest(BaseModel):
    """Request model for fare calculation."""
    journeys: List[Journey] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="List of journeys (max 20 per day)"
    )
    
    @validator('journeys')
    def validate_journey_count(cls, v):
        if len(v) > 20:
            raise ValueError(f"Maximum 20 journeys allowed per day, got {len(v)}")
        return v


class FareResponse(BaseModel):
    """Response model for fare calculation."""
    journeys: List[JourneyWithFare] = Field(
        ...,
        description="List of journeys with calculated fares"
    )
    total_daily_fare: float = Field(..., description="Total fare for all journeys")
    journey_count: int = Field(..., description="Number of journeys")


class FareRule(BaseModel):
    """Model representing a fare rule."""
    from_zone: int
    to_zone: int
    fare: float
    
    @property
    def zone_key(self) -> tuple:
        """Generate a normalized key for zone combination."""
        return tuple(sorted([self.from_zone, self.to_zone]))
