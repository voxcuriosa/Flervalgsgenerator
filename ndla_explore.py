import requests
import json

def explore_ndla_api():
    # Attempt to query NDLA API for "Historie"
    # Based on search results, they use a taxonomy API and GraphQL
    
    # Let's try a simple search or subject lookup first
    # Common endpoint pattern for NDLA might be api.ndla.no
    
    # Try to find subjects via their public API
    # Using a known or likely endpoint for subjects
    
    # Note: Without exact documentation URL, I will try to discover the endpoint
    # or use a general search query if possible.
    
    # Found working endpoint: https://api.ndla.no/taxonomy/v1/nodes?nodetype=SUBJECT
    url = "https://api.ndla.no/taxonomy/v1/nodes?nodetype=SUBJECT"
    print(f"Querying: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Total subjects found: {len(data)}")
            
            # Search for "Vikingtiden" specifically
            viking_nodes = []
            for item in data:
                name = item.get('title') or item.get('name') or ""
                if "viking" in name.lower():
                    viking_nodes.append(item)
            
            print(f"\nFound {len(viking_nodes)} nodes containing 'viking':")
            for node in viking_nodes:
                print(f" - {node.get('title') or node.get('name')} (ID: {node.get('id')})")
                
            if viking_nodes:
                # Pick the most relevant one, likely "Vikingtiden"
                target_id = viking_nodes[0].get('id')
                print(f"\nDeep diving into Vikingtiden ID: {target_id}")
                
                # Get children (topics/articles)
                # Try the taxonomy children endpoint
                children_url = f"https://api.ndla.no/taxonomy/v1/nodes/{target_id}/children"
                # Or maybe it's a topic under Historie vg2, so we should look at its children
                
                print(f"Fetching children from: {children_url}")
                child_resp = requests.get(children_url)
                if child_resp.status_code == 200:
                    children = child_resp.json()
                    print(f"Found {len(children)} items under Vikingtiden.")
                    
                    for child in children:
                        print(f" - {child.get('title') or child.get('name')} (ID: {child.get('id')})")
                        # Check if it has contentUri
                        if child.get('contentUri'):
                            print(f"   Has content: {child.get('contentUri')}")
                else:
                     print(f"Failed to get children: {child_resp.status_code}")
                     
                # Also check the node details for the target itself
                detail_url = f"https://api.ndla.no/taxonomy/v1/nodes/{target_id}"
                d_resp = requests.get(detail_url)
                if d_resp.status_code == 200:
                    details = d_resp.json()
                    print(f"\nDetails for Vikingtiden node:")
                    print(f"Content URI: {details.get('contentUri')}")

                # Try different children endpoint patterns
                child_endpoints = [
                    f"https://api.ndla.no/taxonomy/v1/nodes/{target_id}/children",
                    f"https://ndla.no/api/v1/nodes/{target_id}/children",
                    f"https://api.ndla.no/taxonomy/v1/nodes?parent={target_id}", # Query param style
                    f"https://ndla.no/api/v1/nodes?parent={target_id}"
                ]
                
                for child_url in child_endpoints:
                    print(f"   Trying: {child_url}")
                    try:
                        child_resp = requests.get(child_url)
                        if child_resp.status_code == 200:
                            children = child_resp.json()
                            print(f"   SUCCESS! Found {len(children)} items.")
                            for child in children[:10]: # Limit output
                                print(f"     - {child.get('title') or child.get('name')} (ID: {child.get('id')})")
                            break # Found working endpoint for this subject
                        else:
                            print(f"     Failed: {child_resp.status_code}")
                    except Exception as e:
                        print(f"     Error: {e}")

        else:
            print(f"Failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
    return

            


if __name__ == "__main__":
    explore_ndla_api()
