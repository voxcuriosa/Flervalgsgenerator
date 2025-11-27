import requests
import json

def fetch_resources():
    node_id = "urn:topic:1:b982f745-4f08-4486-8a2f-52357918aa81"
    base_url = "https://api.ndla.no/taxonomy/v1/nodes"
    
    endpoints = [
        f"{base_url}/{node_id}/nodes",
        f"{base_url}/{node_id}/resources"
    ]
    
    for url in endpoints:
        print(f"\nTesting endpoint: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found {len(data)} items.")
                for item in data:
                    print(f"- Name: {item.get('name') or item.get('title')}")
                    print(f"  Type: {item.get('nodeType') or item.get('resourceType')}")
                    print(f"  ID: {item.get('id')}")
                    print(f"  ContentURI: {item.get('contentUri')}")
            else:
                print(f"Failed with status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fetch_resources()
