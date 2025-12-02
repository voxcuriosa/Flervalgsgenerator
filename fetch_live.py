from homey_client import HomeyClient
from storage import save_energy_readings

def fetch_live_data():
    print("Connecting to Homey...")
    client = HomeyClient()
    data = client.get_energy_data()
    
    if data:
        print(f"Fetched {len(data)} devices.")
        # Debug: Print names to verify mapping
        for d in data:
            print(f" - {d['name']}: {d['energy_kwh']} kWh")
            
        if save_energy_readings(data):
            print("Successfully saved to DB.")
        else:
            print("Failed to save to DB.")
    else:
        print("No data found or connection failed.")

if __name__ == "__main__":
    fetch_live_data()
