import os
import sys
from homey_client import HomeyClient
from storage import save_energy_readings

def main():
    print("Starting monthly energy data update...")
    
    # Check for required environment variables
    required_vars = ["HOMEY_ID", "API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    try:
        print("Initializing Homey Client...")
        client = HomeyClient()
        
        print("Fetching energy data from Homey...")
        data = client.get_energy_data()
        
        if data:
            print(f"Successfully fetched data for {len(data)} devices.")
            print("Saving to database...")
            if save_energy_readings(data):
                print("Success! Data saved to database.")
            else:
                print("Error: Failed to save data to database.")
                sys.exit(1)
        else:
            print("Error: No data fetched or could not connect to Homey.")
            sys.exit(1)
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
