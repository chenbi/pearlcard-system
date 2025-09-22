"""
Utility for dynamically extending zones in the PearlCard system.

This script demonstrates how to add new zones without any code changes.
"""

import requests
import json
import sys


def add_zone_via_api(base_url: str = "http://localhost:8000", 
                     zone_number: int = None, 
                     fares_dict: dict = None):
    """
    Add a new zone via the API with dynamic zone number and fares.
    
    Args:
        base_url: API base URL
        zone_number: The zone number to add
        fares_dict: Dictionary mapping existing zones to their fares
    """
    if not zone_number or not fares_dict:
        print("Error: Zone number and fares dictionary are required")
        return
    
    # First, get current zones
    response = requests.get(f"{base_url}/api/fare-rules")
    data = response.json()
    
    print(f"Current zones: {data['available_zones']}")
    print(f"Total zones: {data['total_zones']}")
    
    # Add the new zone
    new_zone_data = {
        "zone_number": zone_number,
        "fares_to_existing_zones": fares_dict
    }
    
    print(f"\nAdding Zone {zone_number}...")
    response = requests.post(
        f"{base_url}/api/zones",
        json=new_zone_data
    )
    
    if response.status_code == 200:
        print(f"✓ Zone {zone_number} added successfully!")
        print(response.json())
    else:
        print(f"✗ Failed to add zone: {response.text}")
    
    # Verify the new zone was added
    response = requests.get(f"{base_url}/api/fare-rules")
    data = response.json()
    print(f"\nUpdated zones: {data['available_zones']}")


def add_zone_interactively():
    """
    Interactively add a new zone by prompting for user input.
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.database import get_db_manager
    
    db_manager = get_db_manager()
    current_zones = db_manager.get_available_zones()
    
    print("=" * 60)
    print("ADD NEW ZONE - INTERACTIVE MODE")
    print("=" * 60)
    print(f"\nCurrent zones: {current_zones}")
    
    try:
        # Get zone number from user
        zone_number = int(input("\nEnter new zone number: "))
        
        if zone_number in current_zones:
            print(f"Error: Zone {zone_number} already exists!")
            return
        
        # Get fares for each existing zone
        fares = {}
        print(f"\nEnter fares from Zone {zone_number} to existing zones:")
        
        for existing_zone in current_zones:
            fare = float(input(f"  Zone {zone_number} → Zone {existing_zone}: £"))
            fares[existing_zone] = fare
        
        # Get same-zone fare
        same_zone_fare = float(input(f"  Zone {zone_number} → Zone {zone_number}: £"))
        fares[zone_number] = same_zone_fare
        
        # Confirm before adding
        print(f"\nAbout to add Zone {zone_number} with fares:")
        for z, f in sorted(fares.items()):
            print(f"  Zone {zone_number} → Zone {z}: £{f}")
        
        confirm = input("\nConfirm? (y/n): ")
        if confirm.lower() == 'y':
            add_zone_via_api(zone_number=zone_number, fares_dict=fares)
        else:
            print("Cancelled.")
            
    except ValueError:
        print("Invalid input. Please enter numbers only.")
    except Exception as e:
        print(f"Error: {e}")


def calculate_fare_by_distance(zone_a: int, zone_b: int) -> float:
    """
    Calculate a suggested fare based on zone distance.
    This is just a helper for generating consistent fares.
    
    Args:
        zone_a: First zone
        zone_b: Second zone
        
    Returns:
        Suggested fare amount
    """
    distance = abs(zone_a - zone_b)
    
    # Simple fare model based on distance
    if distance == 0:
        return 25.0  # Same zone
    elif distance == 1:
        return 45.0  # Adjacent zones
    elif distance == 2:
        return 60.0  # Two zones apart
    elif distance == 3:
        return 75.0  # Three zones apart
    else:
        return 75.0 + (distance - 3) * 10.0  # Far zones


def add_zone_automatically():
    """
    Automatically add the next zone with calculated fares.
    """
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.database import get_db_manager
    
    db_manager = get_db_manager()
    current_zones = db_manager.get_available_zones()
    
    if not current_zones:
        print("No zones found in database")
        return
    
    # Determine next zone number
    next_zone = max(current_zones) + 1
    
    print(f"Current zones: {current_zones}")
    print(f"Adding Zone {next_zone} automatically...")
    
    # Calculate fares based on distance
    fares = {}
    for existing_zone in current_zones:
        fares[existing_zone] = calculate_fare_by_distance(next_zone, existing_zone)
    fares[next_zone] = calculate_fare_by_distance(next_zone, next_zone)
    
    # Display calculated fares
    print(f"\nCalculated fares for Zone {next_zone}:")
    for z, f in sorted(fares.items()):
        print(f"  Zone {next_zone} → Zone {z}: £{f}")
    
    # Add via API
    add_zone_via_api(zone_number=next_zone, fares_dict=fares)


def show_usage():
    """Show usage instructions."""
    print("=" * 60)
    print("ZONE EXTENSION UTILITY")
    print("=" * 60)
    print("\nThis utility helps add new zones to the PearlCard system.")
    print("Zones are stored in the database - no code changes required!")
    print("\nUsage:")
    print("  python extend_zones.py                # Show this help")
    print("  python extend_zones.py interactive    # Add zone interactively")
    print("  python extend_zones.py auto           # Add next zone automatically")
    print("\nExample - Add Zone 5 via curl:")
    print('  curl -X POST http://localhost:8000/api/zones \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"zone_number": 5, "fares_to_existing_zones": ')
    print('         {1: 85, 2: 75, 3: 65, 4: 45, 5: 25}}\'')
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "interactive":
            add_zone_interactively()
        elif command == "auto":
            add_zone_automatically()
        else:
            show_usage()
    else:
        show_usage()
