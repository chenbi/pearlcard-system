"""Fare calculation service implementing business logic."""

from typing import List, Protocol, runtime_checkable
from abc import ABC, abstractmethod

from app.models import Journey, JourneyWithFare, FareResponse
from app.config import settings


@runtime_checkable
class FareCalculatorInterface(Protocol):
    """
    Interface for fare calculation (Dependency Inversion Principle).
    This protocol defines the contract that all fare calculators must follow.
    """
    
    def calculate_single_fare(self, journey: Journey) -> float:
        """Calculate fare for a single journey."""
        ...
    
    def calculate_all_fares(self, journeys: List[Journey]) -> FareResponse:
        """Calculate fares for multiple journeys."""
        ...


class BaseFareCalculator(ABC):
    """Abstract base class for fare calculators (Open/Closed Principle)."""
    
    @abstractmethod
    def calculate_single_fare(self, journey: Journey) -> float:
        """
        Calculate fare for a single journey.
        Must be implemented by subclasses.
        """
        pass
    
    def calculate_all_fares(self, journeys: List[Journey]) -> FareResponse:
        """
        Calculate fares for multiple journeys.
        Default implementation that uses calculate_single_fare.
        Can be overridden if needed for optimization.
        """
        journeys_with_fare = []
        total_fare = 0.0
        
        for idx, journey in enumerate(journeys, 1):
            fare = self.calculate_single_fare(journey)
            journey_with_fare = JourneyWithFare(
                from_zone=journey.from_zone,
                to_zone=journey.to_zone,
                fare=fare,
                journey_id=idx
            )
            journeys_with_fare.append(journey_with_fare)
            total_fare += fare
        
        return FareResponse(
            journeys=journeys_with_fare,
            total_daily_fare=round(total_fare, 2),
            journey_count=len(journeys)
        )


class ZoneBasedFareCalculator(BaseFareCalculator):
    """
    Concrete implementation of fare calculator based on zones.
    Follows Single Responsibility Principle - only handles fare calculation.
    Retrieves fare rules from the local datastore.
    """
    
    def __init__(self):
        """Initialize the fare calculator."""
        pass  # Fare rules are now fetched from database via settings
    
    def calculate_single_fare(self, journey: Journey) -> float:
        """
        Calculate fare for a single journey based on zones.
        Retrieves fare from local datastore.
        
        Args:
            journey: Journey object with from_zone and to_zone
            
        Returns:
            Calculated fare amount from database
        """
        return settings.get_fare(journey.from_zone, journey.to_zone)
    
    # calculate_all_fares is inherited from BaseFareCalculator


# Singleton instance for default calculator
_default_calculator: FareCalculatorInterface = None


def get_fare_calculator() -> FareCalculatorInterface:
    """
    Get the default fare calculator instance (Singleton pattern).
    
    Returns:
        Fare calculator instance implementing FareCalculatorInterface
    """
    global _default_calculator
    if _default_calculator is None:
        _default_calculator = ZoneBasedFareCalculator()
    return _default_calculator
