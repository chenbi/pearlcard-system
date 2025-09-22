"""Unit tests for fare calculation system."""

import pytest
from fastapi.testclient import TestClient
from typing import List
import tempfile
import os

from app.main import app
from app.models import Journey, JourneyRequest, FareResponse
from app.services.fare_calculator import (
    FareCalculatorInterface,
    ZoneBasedFareCalculator
)
from app.config import settings
from app.database import DatabaseManager

# Use a temporary database for testing
test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{test_db.name}"

# Initialize test database
test_db_manager = DatabaseManager(f"sqlite:///{test_db.name}")
test_db_manager.init_default_fare_rules()

# Test client
client = TestClient(app)


class TestModels:
    """Test model validation."""
    
    def test_journey_validation_valid(self):
        """Test valid journey creation."""
        journey = Journey(from_zone=1, to_zone=2)
        assert journey.from_zone == 1
        assert journey.to_zone == 2
    
    def test_journey_validation_invalid_zone(self):
        """Test invalid zone validation."""
        # Zone 0 doesn't exist in database
        with pytest.raises(ValueError):
            Journey(from_zone=0, to_zone=2)
        
        # Zone 99 doesn't exist in database (assuming default setup)
        with pytest.raises(ValueError):
            Journey(from_zone=1, to_zone=99)
    
    def test_journey_request_max_journeys(self):
        """Test maximum journeys validation."""
        journeys = [Journey(from_zone=1, to_zone=1) for _ in range(21)]
        
        with pytest.raises(ValueError):
            JourneyRequest(journeys=journeys)


class TestFareCalculator:
    """Test fare calculation logic."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = ZoneBasedFareCalculator()
    
    def test_single_fare_calculation_same_zone(self):
        """Test fare calculation within same zone."""
        journey = Journey(from_zone=1, to_zone=1)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 40.0
        
        journey = Journey(from_zone=2, to_zone=2)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 35.0
        
        journey = Journey(from_zone=3, to_zone=3)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 30.0
    
    def test_single_fare_calculation_different_zones(self):
        """Test fare calculation between different zones."""
        # Zone 1 to 2
        journey = Journey(from_zone=1, to_zone=2)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 55.0
        
        # Zone 2 to 1 (should be same as 1 to 2)
        journey = Journey(from_zone=2, to_zone=1)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 55.0
        
        # Zone 1 to 3
        journey = Journey(from_zone=1, to_zone=3)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 65.0
        
        # Zone 2 to 3
        journey = Journey(from_zone=2, to_zone=3)
        fare = self.calculator.calculate_single_fare(journey)
        assert fare == 45.0
    
    def test_multiple_fares_calculation(self):
        """Test calculation for multiple journeys."""
        journeys = [
            Journey(from_zone=1, to_zone=2),  # 55
            Journey(from_zone=2, to_zone=3),  # 45
            Journey(from_zone=3, to_zone=3),  # 30
            Journey(from_zone=1, to_zone=1),  # 40
        ]
        
        response = self.calculator.calculate_all_fares(journeys)
        
        assert len(response.journeys) == 4
        assert response.journey_count == 4
        assert response.total_daily_fare == 170.0
        
        # Check individual fares
        assert response.journeys[0].fare == 55.0
        assert response.journeys[1].fare == 45.0
        assert response.journeys[2].fare == 30.0
        assert response.journeys[3].fare == 40.0
    
    
    def test_calculators_implement_protocol(self):
        """Test that all calculators implement the FareCalculatorInterface protocol."""
        calc = ZoneBasedFareCalculator()
        
        # Verify calculator implements the protocol
        assert isinstance(calc, FareCalculatorInterface), \
            f"{calc.__class__.__name__} does not implement FareCalculatorInterface"
        
        # Verify required methods exist
        assert hasattr(calc, 'calculate_single_fare')
        assert hasattr(calc, 'calculate_all_fares')
        
        # Test that methods work correctly
        journey = Journey(from_zone=1, to_zone=2)
        fare = calc.calculate_single_fare(journey)
        assert isinstance(fare, float)
        
        response = calc.calculate_all_fares([journey])
        assert isinstance(response, FareResponse)


class TestAPI:
    """Test API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["version"] == settings.API_VERSION
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_fare_rules_endpoint(self):
        """Test fare rules endpoint."""
        response = client.get("/api/fare-rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "max_journeys_per_day" in data
        assert "available_zones" in data
        assert "datastore" in data
        assert data["max_journeys_per_day"] == 20
        # Don't assume specific zones - just check structure
        assert isinstance(data["available_zones"], list)
    
    def test_calculate_fares_single_journey(self):
        """Test fare calculation for single journey."""
        payload = {
            "journeys": [
                {"from_zone": 1, "to_zone": 2}
            ]
        }
        
        response = client.post("/api/calculate-fares", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["journeys"]) == 1
        assert data["journeys"][0]["fare"] == 55.0
        assert data["total_daily_fare"] == 55.0
        assert data["journey_count"] == 1
    
    def test_calculate_fares_multiple_journeys(self):
        """Test fare calculation for multiple journeys."""
        payload = {
            "journeys": [
                {"from_zone": 1, "to_zone": 1},
                {"from_zone": 1, "to_zone": 2},
                {"from_zone": 2, "to_zone": 3},
                {"from_zone": 3, "to_zone": 3}
            ]
        }
        
        response = client.post("/api/calculate-fares", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["journeys"]) == 4
        assert data["total_daily_fare"] == 170.0
        assert data["journey_count"] == 4
    
    def test_calculate_fares_max_journeys(self):
        """Test maximum journeys limit."""
        payload = {
            "journeys": [
                {"from_zone": 1, "to_zone": 1} for _ in range(20)
            ]
        }
        
        response = client.post("/api/calculate-fares", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["journeys"]) == 20
        assert data["total_daily_fare"] == 800.0  # 20 * 40
    
    def test_calculate_fares_exceeds_max_journeys(self):
        """Test exceeding maximum journeys limit."""
        payload = {
            "journeys": [
                {"from_zone": 1, "to_zone": 1} for _ in range(21)
            ]
        }
        
        response = client.post("/api/calculate-fares", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_calculate_fares_invalid_zone(self):
        """Test invalid zone in request."""
        payload = {
            "journeys": [
                {"from_zone": 0, "to_zone": 2}
            ]
        }
        
        response = client.post("/api/calculate-fares", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_calculate_fares_empty_journeys(self):
        """Test empty journeys list."""
        payload = {
            "journeys": []
        }
        
        response = client.post("/api/calculate-fares", json=payload)
        assert response.status_code == 422  # Validation error


class TestConfiguration:
    """Test configuration settings."""
    
    def test_fare_rules_completeness(self):
        """Test that all zone combinations have fare rules."""
        zones = settings.get_available_zones()  # Get zones from database
        
        for from_zone in zones:
            for to_zone in zones:
                fare = settings.get_fare(from_zone, to_zone)
                assert fare > 0, f"No fare rule for zones {from_zone} to {to_zone}"
    
    def test_zone_validation(self):
        """Test zone validation."""
        zones = settings.get_available_zones()
        
        if zones:  # Only test if zones exist in database
            # Test existing zones are valid
            for zone in zones:
                assert settings.is_valid_zone(zone) == True
            
            # Test invalid zone (one that doesn't exist)
            max_zone = max(zones)
            assert settings.is_valid_zone(max_zone + 100) == False
            assert settings.is_valid_zone(0) == False
        else:
            # If no zones in database, all should be invalid
            assert settings.is_valid_zone(1) == False
            assert settings.is_valid_zone(2) == False
    
    def test_dynamic_zones(self):
        """Test that zones are loaded from database."""
        zones = settings.get_available_zones()
        assert isinstance(zones, list)
        # Don't assume specific zone count - just check it's a list
        
        # If database was initialized, check expected zones exist
        if zones:
            assert all(isinstance(z, int) for z in zones)
    
    def test_min_max_zones(self):
        """Test min and max zone methods."""
        zones = settings.get_available_zones()
        if zones:
            min_zone = settings.get_min_zone()
            max_zone = settings.get_max_zone()
            assert min_zone == min(zones)
            assert max_zone == max(zones)
        else:
            # If no zones, these should handle gracefully
            pass  # No specific assertion for empty database


class TestDatabase:
    """Test database functionality."""
    
    def test_database_initialization(self):
        """Test that database is initialized with default fare rules."""
        from app.database import get_db_manager
        
        db_manager = get_db_manager()
        rules = db_manager.get_all_fare_rules()
        
        # Should have 6 default rules
        assert len(rules) == 6
        
        # Check specific rules
        assert rules.get((1, 1)) == 40.0
        assert rules.get((1, 2)) == 55.0
        assert rules.get((2, 3)) == 45.0
    
    def test_get_fare_from_database(self):
        """Test retrieving fare from database."""
        from app.database import get_db_manager
        
        db_manager = get_db_manager()
        
        # Test exact match
        fare = db_manager.get_fare(1, 2)
        assert fare == 55.0
        
        # Test reversed zones (should work both ways)
        fare = db_manager.get_fare(2, 1)
        assert fare == 55.0
        
        # Test non-existent route
        fare = db_manager.get_fare(1, 5)
        assert fare is None
    
    def test_update_fare_rule(self):
        """Test updating fare rules in database."""
        from app.database import get_db_manager
        
        db_manager = get_db_manager()
        
        # Update existing rule
        original_fare = db_manager.get_fare(1, 1)
        new_fare = 45.0
        
        db_manager.update_fare_rule(1, 1, new_fare)
        updated_fare = db_manager.get_fare(1, 1)
        
        assert updated_fare == new_fare
        
        # Restore original
        db_manager.update_fare_rule(1, 1, original_fare)
    
    def test_config_values(self):
        """Test system configuration storage."""
        from app.database import get_db_manager
        
        db_manager = get_db_manager()
        
        max_journeys = db_manager.get_config_value("max_journeys_per_day")
        assert max_journeys == "20"
        
        # Test non-existent config
        non_existent = db_manager.get_config_value("non_existent_key")
        assert non_existent is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
