import os
import sys
from storage import get_db_connection
from sqlalchemy import text

def main():
    print("--- STARTING CONNECTION TEST ---")
    
    # 1. Test Environment Variables
    print("\n1. Checking Environment Variables...")
    required_vars = ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"❌ MISSING SECRETS: {', '.join(missing)}")
        sys.exit(1)
    else:
        print("✅ All required environment variables are present.")


    # 3. Test Database Connection
    print("\n3. Testing Database Connection...")
    try:
        engine = get_db_connection()
        if not engine:
            print("❌ Database Connection FAILED: Could not create engine (check credentials).")
            sys.exit(1)
            
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database Connection SUCCESS! Executed 'SELECT 1'.")
            
    except Exception as e:
        print(f"❌ Database Connection FAILED: {e}")
        sys.exit(1)

    print("\n--- TEST COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    main()
