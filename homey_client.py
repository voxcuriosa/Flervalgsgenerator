import requests
import pandas as pd
from datetime import datetime, timedelta
import os

class HomeyClient:
    def __init__(self):
        # Try to get credentials from environment variables first (for GitHub Actions)
        self.homey_id = os.environ.get("HOMEY_ID")
        self.api_key = os.environ.get("API_KEY")
        
        # Fallback to hardcoded values (for local testing if env vars missing)
        if not self.homey_id:
            self.homey_id = "5c9096191244054e36667527"
        if not self.api_key:
            self.api_key = "490a6d05-9551-4e43-9b43-46d332661596"
            
        self.base_url = f"https://{self.homey_id}.connect.athom.com/api/manager/insights"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_energy_data(self):
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return []
            
            devices = response.json()
            energy_devices = []
            
            # Name Mapping (Canonical Name <- Homey Name)
            # Homey Name might have trailing spaces or be different
            NAME_MAPPING = {
                "Bad": "Bad - Varmekabler",
                "Bad - Varmekabler ": "Bad - Varmekabler",
                "Bad kjeller": "Bad kjeller - Varmekabler",
                "Bad kjeller - Varmekabler ": "Bad kjeller - Varmekabler",
                "Stue - Varmekabler ": "Stue",
                "Stue - Varmekabler": "Stue",
                "Kjellergang - Varme": "Kjellergang",
                "Casper - Varme": "Casper",
                "Cornelius - Varmekabler ": "Cornelius",
                "Cornelius - Varmekabler": "Cornelius",
                "Varmepumpe ": "Varmepumpe",
                "Vindfang - Varmekabler": "Vindfang", # Assumption
                "Vindfang - Varmekabler ": "Vindfang",
                "CBV  (EHVKFY9X)": "Easee",
            }
            
            IGNORED_DEVICES = ["Vann", "Vann ", "Tibber puls", "Tibber puls "]

            for dev_id, dev in devices.items():
                caps = dev.get('capabilities', [])
                if 'meter_power' in caps: # Only interested in devices that measure total energy
                    name = dev.get('name', 'Unknown')
                    
                    if name in IGNORED_DEVICES:
                        continue
                        
                    # Apply mapping
                    if name in NAME_MAPPING:
                        name = NAME_MAPPING[name]
                        
                    capabilitiesObj = dev.get('capabilitiesObj', {})
                    
                    # Current Power (W)
                    power_w = 0
                    if 'measure_power' in capabilitiesObj:
                        power_w = capabilitiesObj['measure_power'].get('value', 0)
                        
                    # Total Energy (kWh)
                    energy_kwh = 0
                    if 'meter_power' in capabilitiesObj:
                        energy_kwh = capabilitiesObj['meter_power'].get('value', 0)
                        
                    energy_devices.append({
                        "id": dev_id,
                        "name": name,
                        "power_w": power_w,
                        "energy_kwh": energy_kwh,
                        "timestamp": datetime.now()
                    })
            
            return energy_devices
        except Exception as e:
            print(f"Error fetching Homey data: {e}")
            return []

    def get_energy_dataframe(self):
        data = self.get_energy_data()
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
