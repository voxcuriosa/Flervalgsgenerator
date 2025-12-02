import requests

homey_id = "65abb7fff169f294d54ef2f4"
full_key = "4031c90e-348c-4b76-8f54-ef38b546081d:62ce7efa-9615-4004-b60b-53f3978f81fc:f94e3d39babfb9936746cf3a7f02a3712e7e62d1"

def test_devices(hid, key):
    url = f"https://{hid}.connect.athom.com/api/manager/devices/device"
    headers = {
        "Authorization": f"Bearer {key}"
    }
    print(f"Testing Devices -> {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            devices = response.json()
            print(f"Success! Found {len(devices)} devices.")
            # Print names of first 5 devices
            for dev_id, dev in list(devices.items())[:5]:
                print(f"- {dev.get('name')} (ID: {dev_id})")
                # Check for energy capabilities
                caps = dev.get('capabilities', [])
                if 'measure_power' in caps or 'meter_power' in caps:
                    print(f"  Energy Capabilities: {caps}")
                    # Try to get current value
                    capabilitiesObj = dev.get('capabilitiesObj', {})
                    if 'measure_power' in capabilitiesObj:
                        print(f"  Current Power: {capabilitiesObj['measure_power'].get('value')} W")
                    if 'meter_power' in capabilitiesObj:
                        print(f"  Total Energy: {capabilitiesObj['meter_power'].get('value')} kWh")
            return True
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    return False

test_devices(homey_id, full_key)
