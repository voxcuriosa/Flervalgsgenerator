import os
import sys
from homey_client import HomeyClient
from storage import get_db_connection
from sqlalchemy import text

def main():
    print("--- STARTING CONNECTION TEST ---")
    
    # 1. Test Environment Variables
    print("\n1. Checking Environment Variables...")
    required_vars = ["HOMEY_ID", "API_KEY", "POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"❌ MISSING SECRETS: {', '.join(missing)}")
        sys.exit(1)
    else:
        print("✅ All required environment variables are present.")

    # 2. Test Homey Connection
    print("\n2. Testing Homey Connection...")
    try:
        client = HomeyClient()
        data = client.get_energy_data()
        if data:
            print(f"✅ Homey Connection SUCCESS! Fetched {len(data)} devices.")
        else:
            print("⚠️ Homey Connection: Connected, but no data returned (or empty).")
    except Exception as e:
        print(f"❌ Homey Connection FAILED: {e}")
        sys.exit(1)

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
