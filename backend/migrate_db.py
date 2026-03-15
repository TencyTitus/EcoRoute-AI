from app.database import engine
from sqlalchemy import text

def migrate():
    print("🚀 Starting Database Migration...")
    try:
        with engine.begin() as conn:
            # Add engine_size if it doesn't exist
            try:
                conn.execute(text("ALTER TABLE vehicles ADD COLUMN engine_size FLOAT DEFAULT 2.0"))
                print("✅ Added column: engine_size")
            except Exception as e:
                print(f"ℹ️ Could not add engine_size: {e}")
            
            # Add cylinders if it doesn't exist
            try:
                conn.execute(text("ALTER TABLE vehicles ADD COLUMN cylinders INTEGER DEFAULT 4"))
                print("✅ Added column: cylinders")
            except Exception as e:
                print(f"ℹ️ Could not add cylinders: {e}")

            try:
                conn.execute(text("ALTER TABLE delivery_points ADD COLUMN notes VARCHAR(1000)"))
                print("✅ Added column: delivery_points.notes")
            except Exception as e:
                print(f"ℹ️ Could not add notes to delivery_points: {e}")

            # Add created_by_id to optimized_routes
            try:
                conn.execute(text("ALTER TABLE optimized_routes ADD COLUMN created_by_id INTEGER REFERENCES users(id)"))
                print("✅ Added column: optimized_routes.created_by_id")
            except Exception as e:
                print(f"ℹ️ Could not add created_by_id: {e}")
            
        print("✨ Migration complete!")
    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    migrate()
