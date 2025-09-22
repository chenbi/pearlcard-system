#!/usr/bin/env python3
"""
Database management utility for PearlCard system.

Usage:
    python manage_db.py init      - Initialize database with default rules
    python manage_db.py show      - Show all fare rules
    python manage_db.py update    - Update a fare rule
    python manage_db.py add_zone  - Add a new zone
    python manage_db.py reset     - Reset to default rules
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DatabaseManager


def init_database():
    """Initialize database with default fare rules."""
    print("Initializing database...")
    db = DatabaseManager()
    db.init_default_fare_rules()
    print("Database initialized successfully!")
    show_rules()


def show_rules():
    """Display all fare rules."""
    db = DatabaseManager()
    rules = db.get_all_fare_rules()
    
    print("\n" + "="*50)
    print("CURRENT FARE RULES IN LOCAL DATASTORE")
    print("="*50)
    print(f"{'From Zone':<10} {'To Zone':<10} {'Fare (£)':<10}")
    print("-"*30)
    
    for (from_zone, to_zone), fare in sorted(rules.items()):
        print(f"{from_zone:<10} {to_zone:<10} £{fare:<10.2f}")
    
    print("-"*30)
    print(f"Total rules: {len(rules)}")
    
    # Show system config
    max_journeys = db.get_config_value("max_journeys_per_day")
    print(f"\nMax journeys per day: {max_journeys}")
    print("="*50)


def update_rule():
    """Interactive fare rule update."""
    print("\nUPDATE FARE RULE")
    print("-"*30)
    
    try:
        db = DatabaseManager()
        available_zones = db.get_available_zones()
        
        print(f"Available zones: {available_zones}")
        
        from_zone = int(input("Enter from zone: "))
        to_zone = int(input("Enter to zone: "))
        
        if from_zone not in available_zones or to_zone not in available_zones:
            print(f"Invalid zone numbers! Must be one of: {available_zones}")
            return
        
        current_fare = db.get_fare(from_zone, to_zone)
        
        if current_fare:
            print(f"Current fare: £{current_fare}")
        else:
            print("No existing rule for this route.")
        
        new_fare = float(input("Enter new fare (£): "))
        
        if new_fare <= 0:
            print("Fare must be positive!")
            return
        
        db.update_fare_rule(from_zone, to_zone, new_fare)
        print(f"✓ Updated fare for Zone {from_zone} → Zone {to_zone} to £{new_fare}")
        
    except ValueError:
        print("Invalid input! Please enter numbers only.")
    except Exception as e:
        print(f"Error updating rule: {e}")


def reset_database():
    """Reset database to default rules."""
    confirm = input("Are you sure you want to reset all fare rules to defaults? (yes/no): ")
    
    if confirm.lower() == 'yes':
        import os
        db_path = "./pearlcard_fare_rules.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Database deleted.")
        
        init_database()
        print("Database reset to defaults!")
    else:
        print("Reset cancelled.")


def add_new_zone():
    """Add a new zone interactively."""
    print("\nADD NEW ZONE")
    print("-"*30)
    
    try:
        db = DatabaseManager()
        existing_zones = db.get_available_zones()
        
        print(f"Current zones: {existing_zones}")
        
        zone_number = int(input("\nEnter new zone number: "))
        
        if zone_number in existing_zones:
            print(f"Zone {zone_number} already exists!")
            return
        
        print(f"\nEnter fares from Zone {zone_number} to existing zones:")
        fares = {}
        
        # Get fare to each existing zone
        for existing_zone in existing_zones:
            fare = float(input(f"  Zone {zone_number} → Zone {existing_zone}: £"))
            fares[existing_zone] = fare
        
        # Get same-zone fare
        same_zone_fare = float(input(f"  Zone {zone_number} → Zone {zone_number}: £"))
        fares[zone_number] = same_zone_fare
        
        # Add the zone
        db.add_zone(zone_number, fares)
        
        print(f"\n✓ Zone {zone_number} added successfully!")
        show_rules()
        
    except ValueError:
        print("Invalid input! Please enter numbers only.")
    except Exception as e:
        print(f"Error adding zone: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'init': init_database,
        'show': show_rules,
        'update': update_rule,
        'reset': reset_database,
        'add_zone': add_new_zone
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
