"""Database models and setup for PearlCard system."""

from sqlalchemy import create_engine, Column, Integer, Float, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Set
import os

Base = declarative_base()


class FareRuleDB(Base):
    """Database model for storing fare rules."""
    __tablename__ = "fare_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    from_zone = Column(Integer, nullable=False)
    to_zone = Column(Integer, nullable=False)
    fare = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    
    # Ensure unique combination of from_zone and to_zone
    __table_args__ = (
        UniqueConstraint('from_zone', 'to_zone', name='_zone_pair_uc'),
    )
    
    def __repr__(self):
        return f"<FareRule(from_zone={self.from_zone}, to_zone={self.to_zone}, fare={self.fare})>"


class SystemConfigDB(Base):
    """Database model for storing system configuration."""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value})>"


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database connection."""
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "sqlite:///./pearlcard_fare_rules.db"
        )
        
        # Create engine with appropriate settings for SQLite
        connect_args = {"check_same_thread": False} if "sqlite" in self.database_url else {}
        self.engine = create_engine(self.database_url, connect_args=connect_args)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def init_default_fare_rules(self):
        """Initialize database with default fare rules."""
        # Default rules for initial zones 1-3
        default_rules = [
            (1, 1, 40.0, "Zone 1 to Zone 1"),
            (1, 2, 55.0, "Zone 1 to Zone 2"),
            (1, 3, 65.0, "Zone 1 to Zone 3"),
            (2, 2, 35.0, "Zone 2 to Zone 2"),
            (2, 3, 45.0, "Zone 2 to Zone 3"),
            (3, 3, 30.0, "Zone 3 to Zone 3"),
        ]
        
        session = self.get_session()
        try:
            # Check if rules already exist
            existing_count = session.query(FareRuleDB).count()
            if existing_count == 0:
                # Add default rules
                for from_zone, to_zone, fare, desc in default_rules:
                    rule = FareRuleDB(
                        from_zone=from_zone,
                        to_zone=to_zone,
                        fare=fare,
                        description=desc
                    )
                    session.add(rule)
                session.commit()
                print(f"Initialized {len(default_rules)} default fare rules")
            
            # Initialize system config
            existing_config = session.query(SystemConfigDB).filter_by(key="max_journeys_per_day").first()
            if not existing_config:
                config = SystemConfigDB(
                    key="max_journeys_per_day",
                    value="20",
                    description="Maximum number of journeys allowed per day"
                )
                session.add(config)
                session.commit()
                print("Initialized system configuration")
                
        finally:
            session.close()
    
    def get_all_fare_rules(self):
        """Retrieve all fare rules from database."""
        session = self.get_session()
        try:
            rules = session.query(FareRuleDB).all()
            return {
                (rule.from_zone, rule.to_zone): rule.fare
                for rule in rules
            }
        finally:
            session.close()
    
    def get_available_zones(self) -> list:
        """Get all unique zones from the database."""
        session = self.get_session()
        try:
            rules = session.query(FareRuleDB).all()
            zones = set()
            for rule in rules:
                zones.add(rule.from_zone)
                zones.add(rule.to_zone)
            return sorted(list(zones)) if zones else []  # Return empty list if no zones
        finally:
            session.close()
    
    def get_min_max_zones(self) -> tuple:
        """Get minimum and maximum zone numbers."""
        zones = self.get_available_zones()
        if zones:
            return min(zones), max(zones)
        return None, None  # No defaults if database is empty
    
    def is_valid_zone(self, zone: int) -> bool:
        """Check if a zone number exists in the database."""
        zones = self.get_available_zones()
        return zone in zones
    
    def get_fare(self, from_zone: int, to_zone: int) -> Optional[float]:
        """Get fare for a specific zone pair."""
        session = self.get_session()
        try:
            # Try exact match first
            rule = session.query(FareRuleDB).filter_by(
                from_zone=from_zone,
                to_zone=to_zone
            ).first()
            
            if rule:
                return rule.fare
            
            # Try reversed zones (since fare is same both ways)
            rule = session.query(FareRuleDB).filter_by(
                from_zone=to_zone,
                to_zone=from_zone
            ).first()
            
            return rule.fare if rule else None
        finally:
            session.close()
    
    def add_zone(self, zone_number: int, fares_to_existing_zones: dict):
        """
        Add a new zone with fare rules to all existing zones.
        
        Args:
            zone_number: The new zone number
            fares_to_existing_zones: Dict mapping existing zones to fares
                                    e.g., {1: 75.0, 2: 60.0, 3: 50.0, 4: 25.0}
        """
        session = self.get_session()
        try:
            for existing_zone, fare in fares_to_existing_zones.items():
                # Add fare rule for new zone to existing zone
                rule = FareRuleDB(
                    from_zone=zone_number,
                    to_zone=existing_zone,
                    fare=fare,
                    description=f"Zone {zone_number} to Zone {existing_zone}"
                )
                session.add(rule)
            
            session.commit()
            print(f"Added Zone {zone_number} with {len(fares_to_existing_zones)} fare rules")
        finally:
            session.close()
    
    def update_fare_rule(self, from_zone: int, to_zone: int, new_fare: float):
        """Update or create a fare rule."""
        session = self.get_session()
        try:
            rule = session.query(FareRuleDB).filter_by(
                from_zone=from_zone,
                to_zone=to_zone
            ).first()
            
            if rule:
                rule.fare = new_fare
            else:
                rule = FareRuleDB(
                    from_zone=from_zone,
                    to_zone=to_zone,
                    fare=new_fare,
                    description=f"Zone {from_zone} to Zone {to_zone}"
                )
                session.add(rule)
            
            session.commit()
            return rule
        finally:
            session.close()
    
    def get_config_value(self, key: str) -> Optional[str]:
        """Get a configuration value by key."""
        session = self.get_session()
        try:
            config = session.query(SystemConfigDB).filter_by(key=key).first()
            return config.value if config else None
        finally:
            session.close()


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get singleton database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.init_default_fare_rules()
    return _db_manager
