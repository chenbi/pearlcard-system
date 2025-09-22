"""Configuration for the PearlCard system."""

from typing import Dict, Tuple, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # API Settings
    API_TITLE = "PearlCard Fare Calculator"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = (
        "NFC-enabled prepaid card fare calculation system with local datastore"
    )

    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pearlcard_fare_rules.db")

    # CORS Settings
    CORS_ORIGINS = [
        "http://163.192.43.3:3000",
        "163.192.43.3:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # System Constraints - will be loaded from database
    MAX_JOURNEYS_PER_DAY = 20

    # Cached fare rules and zones (loaded from database)
    _fare_rules_cache: Optional[Dict[Tuple[int, int], float]] = None
    _zones_cache: Optional[list] = None

    @classmethod
    def get_fare_rules(cls) -> Dict[Tuple[int, int], float]:
        """
        Get fare rules from database (with caching).
        Falls back to hardcoded values if database is unavailable.
        """
        if cls._fare_rules_cache is None:
            try:
                from app.database import get_db_manager

                db_manager = get_db_manager()
                cls._fare_rules_cache = db_manager.get_all_fare_rules()
            except Exception as e:
                print(f"Warning: Could not load fare rules from database: {e}")
                # Fallback to minimal default rules
                cls._fare_rules_cache = {
                    (1, 1): 40.0,
                    (1, 2): 55.0,
                    (1, 3): 65.0,
                    (2, 2): 35.0,
                    (2, 3): 45.0,
                    (3, 3): 30.0,
                }
        return cls._fare_rules_cache

    @classmethod
    def get_fare(cls, from_zone: int, to_zone: int) -> float:
        """
        Get fare for a journey between two zones.
        Uses caching for performance with millions of users.

        Args:
            from_zone: Starting zone
            to_zone: Ending zone

        Returns:
            Fare amount for the journey
        """
        # Try cache-enabled path first
        try:
            from app.cache import get_fare_with_cache

            return get_fare_with_cache(from_zone, to_zone)
        except ImportError:
            # Fallback to direct database access if cache not available
            pass

        # Original database logic
        try:
            from app.database import get_db_manager

            db_manager = get_db_manager()
            fare = db_manager.get_fare(from_zone, to_zone)
            if fare is not None:
                return fare
        except:
            pass

        # Fallback to cached rules
        fare_rules = cls.get_fare_rules()
        zone_key = tuple(sorted([from_zone, to_zone]))
        return fare_rules.get(zone_key, 0.0)

    @classmethod
    def reload_fare_rules(cls):
        """Force reload of fare rules and zones from database."""
        cls._fare_rules_cache = None
        cls._zones_cache = None
        cls.get_fare_rules()
        cls.get_available_zones()

    @classmethod
    def is_valid_zone(cls, zone: int) -> bool:
        """Check if a zone number is valid (exists in database)."""
        try:
            from app.database import get_db_manager

            db_manager = get_db_manager()
            return db_manager.is_valid_zone(zone)
        except Exception as e:
            # If database is not available, reject all zones
            print(f"Warning: Cannot validate zone {zone}, database error: {e}")
            return False

    @classmethod
    def get_available_zones(cls) -> list:
        """Get list of available zones from database."""
        if cls._zones_cache is None:
            try:
                from app.database import get_db_manager

                db_manager = get_db_manager()
                cls._zones_cache = db_manager.get_available_zones()
            except Exception as e:
                print(f"Warning: Cannot load zones from database: {e}")
                cls._zones_cache = []  # Empty list if database unavailable
        return cls._zones_cache

    @classmethod
    def get_min_zone(cls) -> int:
        """Get minimum zone number."""
        zones = cls.get_available_zones()
        return min(zones) if zones else 1

    @classmethod
    def get_max_zone(cls) -> int:
        """Get maximum zone number."""
        zones = cls.get_available_zones()
        return max(zones) if zones else 3


settings = Settings()
