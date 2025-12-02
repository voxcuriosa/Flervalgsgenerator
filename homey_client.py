import requests
import pandas as pd
from datetime import datetime

HOMEY_ID = "65abb7fff169f294d54ef2f4"
API_KEY = "4031c90e-348c-4b76-8f54-ef38b546081d:62ce7efa-9615-4004-b60b-53f3978f81fc:f94e3d39babfb9936746cf3a7f02a3712e7e62d1"

class HomeyClient:
    def __init__(self):
        self.base_url = f"https://{HOMEY_ID}.connect.athom.com/api/manager/devices/device"
        self.headers = {
            "Authorization": f"Bearer {API_KEY}"
        }

    def get_energy_data(self):
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return []
            
            devices = response.json()
            energy_devices = []
            
            for dev_id, dev in devices.items():
                caps = dev.get('capabilities', [])
                if 'meter_power' in caps: # Only interested in devices that measure total energy
                    name = dev.get('name', 'Unknown')
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
