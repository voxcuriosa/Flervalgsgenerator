import requests
import json

def get_node_details(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def get_nodes(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/nodes"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error nodes: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception nodes: {e}")
        return []

node_id = "urn:topic:b570bf11-a1d9-4538-ba40-1dd5378f52e1"
print("Details:")
print(json.dumps(get_node_details(node_id), indent=2))
print("\nChildren:")
print(json.dumps(get_nodes(node_id), indent=2))
