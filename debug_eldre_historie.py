import requests
import json

def debug_eldre_historie():
    node_id = "urn:topic:1:00d325d9-d87a-4ef6-9514-7017b0e6a291" # Eldre historie
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/nodes"
    
    print(f"Fetching children for: {node_id}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        print(f"Found {len(data)} children:")
        for child in data:
            print(f"- Name: {child.get('name')}")
            print(f"  ID: {child.get('id')}")
            print(f"  Type: {child.get('nodeType')}")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_eldre_historie()
