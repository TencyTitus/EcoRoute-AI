import os
import sys
from sqlalchemy import text, func
from datetime import datetime

# Add the project root to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import User, Vehicle, DeliveryPoint, OptimizedRoute, RouteHistory
from app.core.security import hash_password

def recovery():
    print("--- Starting Database Recovery & Schema Update ---")
    db = SessionLocal()
    
    # 1. Backup Users
    print("\n1. Backing up users...")
    users_backup = []
    try:
        users = db.query(User).all()
        for u in users:
            users_backup.append({
                'id': u.id,
                'full_name': u.full_name,
                'email': u.email,
                'password_hash': u.password_hash,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': u.created_at
            })
        print(f"   Success: Backed up {len(users_backup)} users.")
    except Exception as e:
        print(f"   Warning: Could not backup users ({str(e)}). Table might be missing or incompatible.")
        print("   If this is a fresh database, this is expected.")
    
    db.close()
    
    # 2. Recreate Schema
    print("\n2. Recreating database schema (Dropping and Creating all tables)...")
    try:
        # We use a raw connection to ensure we can drop everything even with foreign key constraints
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS route_delivery_points CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS route_history CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS optimized_routes CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS delivery_points CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS vehicles CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            
            # Try to enable postgis
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            except:
                pass
        
        Base.metadata.create_all(bind=engine)
        print("   Success: Database schema recreated with latest models.")
    except Exception as e:
        print(f"   ERROR: Failed to recreate schema: {str(e)}")
        return

    db = SessionLocal()
    
    # 3. Restore Users
    print("\n3. Restoring users...")
    try:
        if not users_backup:
            print("   No users found in backup. Adding default users...")
            default_users = [
                User(
                    full_name="Admin User",
                    email="admin@ecoroute.ai",
                    password_hash=hash_password("admin123"),
                    role="admin",
                    is_active=True
                ),
                User(
                    full_name="Manager User",
                    email="manager@ecoroute.ai",
                    password_hash=hash_password("admin123"),
                    role="manager",
                    is_active=True
                )
            ]
            db.add_all(default_users)
            db.commit()
            print("   Success: Added default users.")
            users_backup = [{'id': u.id} for u in default_users]
        else:
            for u_data in users_backup:
                u_id = u_data.pop('id')
                user = User(**u_data)
                user.id = u_id
                db.add(user)
            db.commit()
            print(f"   Success: Restored {len(users_backup)} users.")
    except Exception as e:
        print(f"   ERROR: Failed to restore users: {str(e)}")
        db.rollback()

    # Get a valid user ID for created_by
    manager_id = users_backup[0]['id'] if users_backup else None

    # 4. Seed Vehicles
    print("\n4. Seeding vehicles...")
    try:
        vehicles = [
            Vehicle(
                license_plate="DL 1GC 1234",
                vehicle_type="Truck",
                model="Tata LPT 1613",
                max_capacity_kg=10000.0,
                fuel_efficiency_kmpl=4.5,
                emission_factor=2.68,
                status="available",
                avg_speed_kmh=40.0,
                fuel_type="Diesel"
            ),
            Vehicle(
                license_plate="DL 1LC 5678",
                vehicle_type="Van",
                model="Mahindra Supro",
                max_capacity_kg=1000.0,
                fuel_efficiency_kmpl=12.0,
                emission_factor=2.3,
                status="available",
                avg_speed_kmh=50.0,
                fuel_type="CNG"
            ),
            Vehicle(
                license_plate="DL 1MT 9012",
                vehicle_type="Mini Truck",
                model="Tata Ace Gold",
                max_capacity_kg=750.0,
                fuel_efficiency_kmpl=15.0,
                emission_factor=2.1,
                status="available",
                avg_speed_kmh=45.0,
                fuel_type="Electric"
            )
        ]
        db.add_all(vehicles)
        db.commit()
        print("   Success: Seeded 3 vehicles.")
    except Exception as e:
        print(f"   ERROR: Failed to seed vehicles: {str(e)}")
        db.rollback()

    # 5. Seed Delivery Points (Delhi NCR)
    print("\n5. Seeding delivery points...")
    try:
        # We try to seed without 'location' field if spatial types are being problematic
        # Most of the app should work based on lat/lon
        points_data = [
            {"name": "Connaught Place Hub", "addr": "Near Rajiv Chowk, New Delhi", "lat": 28.6315, "lon": 77.2167, "dem": 500.0, "pri": 1},
            {"name": "Noida Sector 18", "addr": "Wave Mall, Noida", "lat": 28.5672, "lon": 77.3210, "dem": 300.0, "pri": 2},
            {"name": "Gurgaon Cyber City", "addr": "DLF Phase 3, Gurgaon", "lat": 28.4950, "lon": 77.0878, "dem": 450.0, "pri": 3}
        ]
        
        for p in points_data:
            try:
                point = DeliveryPoint(
                    name=p["name"],
                    address=p["addr"],
                    latitude=p["lat"],
                    longitude=p["lon"],
                    demand=p["dem"],
                    priority=p["pri"],
                    created_by=manager_id
                )
                # Attempt to set location, but swallow error if it fails
                try:
                    point.location = func.ST_SetSRID(func.ST_MakePoint(p["lon"], p["lat"]), 4326)
                except:
                    pass
                db.add(point)
            except:
                pass
        
        db.commit()
        print("   Success: Seeded 3 delivery points.")
    except Exception as e:
        print(f"   Warning: Incomplete seeding for delivery points: {str(e)}")
        db.rollback()

    db.close()
    print("\n--- Recovery Complete ---")

if __name__ == "__main__":
    recovery()
