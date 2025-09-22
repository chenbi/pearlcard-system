"""API endpoints for fare calculation."""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional

from app.models import JourneyRequest, FareResponse
from app.services import get_fare_calculator
from app.services.fare_calculator import FareCalculatorInterface
from app.config import settings
from app.database import get_db_manager

router = APIRouter(prefix="/api", tags=["Fare Calculation"])


def get_calculator() -> FareCalculatorInterface:
    """
    Dependency injection for fare calculator.
    Returns any implementation of FareCalculatorInterface.
    """
    return get_fare_calculator()


@router.post("/calculate-fares", response_model=FareResponse)
async def calculate_fares(
    request: JourneyRequest,
    calculator: FareCalculatorInterface = Depends(get_calculator)
) -> FareResponse:
    """
    Calculate fares for a list of journeys.
    
    Note: calculator is injected as FareCalculatorInterface,
    allowing any implementation to be used (Dependency Inversion Principle).
    
    Args:
        request: Journey request containing list of journeys
        calculator: Injected fare calculator implementing FareCalculatorInterface
        
    Returns:
        FareResponse with calculated fares and total
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate journey count
        if len(request.journeys) > settings.MAX_JOURNEYS_PER_DAY:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {settings.MAX_JOURNEYS_PER_DAY} journeys allowed per day"
            )
        
        # Calculate fares
        response = calculator.calculate_all_fares(request.journeys)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/fare-rules")
async def get_fare_rules():
    """
    Get all fare rules from the local datastore.
    
    Returns:
        Dictionary of fare rules from database
    """
    db_manager = get_db_manager()
    rules_dict = db_manager.get_all_fare_rules()
    
    rules = []
    for (from_zone, to_zone), fare in rules_dict.items():
        rules.append({
            "from_zone": from_zone,
            "to_zone": to_zone,
            "fare": fare,
            "description": f"Zone {from_zone} to Zone {to_zone}"
        })
    
    # Get max journeys from database config
    max_journeys = db_manager.get_config_value("max_journeys_per_day")
    
    # Get available zones dynamically from database
    available_zones = db_manager.get_available_zones()
    
    return {
        "rules": rules,
        "max_journeys_per_day": int(max_journeys) if max_journeys else settings.MAX_JOURNEYS_PER_DAY,
        "available_zones": available_zones,
        "min_zone": min(available_zones) if available_zones else None,
        "max_zone": max(available_zones) if available_zones else None,
        "total_zones": len(available_zones),
        "datastore": "SQLite Local Database"
    }


@router.put("/fare-rules")
async def update_fare_rule(
    from_zone: int = Body(..., ge=1),
    to_zone: int = Body(..., ge=1),
    fare: float = Body(..., gt=0)
):
    """
    Update a fare rule in the local datastore.
    
    Args:
        from_zone: Starting zone
        to_zone: Ending zone
        fare: New fare amount
        
    Returns:
        Updated fare rule
    """
    # Validate zones exist in database
    if not settings.is_valid_zone(from_zone) or not settings.is_valid_zone(to_zone):
        available_zones = settings.get_available_zones()
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid zone numbers. Available zones: {available_zones}"
        )
    
    db_manager = get_db_manager()
    rule = db_manager.update_fare_rule(from_zone, to_zone, fare)
    
    # Clear cache to ensure new rules are loaded
    settings.reload_fare_rules()
    
    return {
        "from_zone": rule.from_zone,
        "to_zone": rule.to_zone,
        "fare": rule.fare,
        "message": "Fare rule updated successfully in local datastore"
    }


@router.post("/zones")
async def add_new_zone(
    zone_number: int = Body(..., ge=1),
    fares_to_existing_zones: dict = Body(...)
):
    """
    Add a new zone with fare rules to all existing zones.
    
    Args:
        zone_number: The new zone number
        fares_to_existing_zones: Dict mapping existing zones to fares
                                e.g., {1: 75.0, 2: 60.0, 3: 50.0}
    
    Returns:
        Success message with new zone details
    """
    db_manager = get_db_manager()
    
    # Check if zone already exists
    if db_manager.is_valid_zone(zone_number):
        raise HTTPException(
            status_code=400,
            detail=f"Zone {zone_number} already exists"
        )
    
    # Validate all existing zones are covered
    existing_zones = db_manager.get_available_zones()
    
    # Add self-fare (same zone travel)
    if zone_number not in fares_to_existing_zones:
        raise HTTPException(
            status_code=400,
            detail=f"Must provide fare for Zone {zone_number} to Zone {zone_number}"
        )
    
    # Add the new zone
    db_manager.add_zone(zone_number, fares_to_existing_zones)
    
    # Clear cache
    settings.reload_fare_rules()
    
    return {
        "message": f"Zone {zone_number} added successfully",
        "new_zone": zone_number,
        "fare_rules_added": len(fares_to_existing_zones),
        "total_zones": len(db_manager.get_available_zones())
    }


@router.get("/health")
async def health_check():
    """Health check endpoint including database status."""
    db_status = "healthy"
    try:
        db_manager = get_db_manager()
        rules_count = len(db_manager.get_all_fare_rules())
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        rules_count = 0
    
    return {
        "status": "healthy",
        "service": "PearlCard Fare Calculator",
        "datastore_status": db_status,
        "fare_rules_count": rules_count
    }
