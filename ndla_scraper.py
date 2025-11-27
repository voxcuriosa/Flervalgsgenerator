import requests
import json
import time

def scrape_ndla_history():
    # IDs found in exploration
    subjects = {
        "Historie vg2": "urn:subject:1:ff69c291-6374-4766-80c2-47d5840d8bbf",
        "Historie vg3": "urn:subject:cc109c51-a083-413b-b497-7f80a0569a92"
    }
    
    for subject_name, subject_id in subjects.items():
        print(f"\n{'='*40}")
        print(f"Analyzing {subject_name} (ID: {subject_id})")
        print(f"{'='*40}")
        
        # Using the working endpoint found: ?parent={id}
        # Note: This seems to return a flat list of ALL descendants or immediate children?
        # The count 9476 for vg3 suggests it might be recursive or just a lot of nodes.
        url = f"https://api.ndla.no/taxonomy/v1/nodes?parent={subject_id}&page-size=10000"
        
        try:
            print(f"Fetching data from: {url}")
            response = requests.get(url)
            
            if response.status_code == 200:
                nodes = response.json()
                print(f"Total nodes found: {len(nodes)}")
                
                # Analyze node types
                node_types = {}
                articles = []
                viking_nodes = [] # Initialize viking_nodes list
                
                for node in nodes:
                    n_type = node.get('nodeType')
                    node_types[n_type] = node_types.get(n_type, 0) + 1
                    
                    # Identify articles/fagstoff
                    # Usually 'ARTICLE' or similar. Let's look for likely candidates.
                    if n_type == 'ARTICLE':
                        articles.append(node)

                    # Check for "Viking" in title or name for further inspection
                    title = (node.get('title') or "").lower()
                    name = (node.get('name') or "").lower()
                    if "viking" in title or "viking" in name:
                        viking_nodes.append(node)
                
                print("\nNode Type Distribution:")
                for n_type, count in node_types.items():
                    print(f" - {n_type}: {count}")
                
                # New block: Inspect all Viking nodes and try content fetch
                if viking_nodes:
                    print(f"\nInspecting ALL Viking nodes to find the main Topic vs Articles:")
                    
                    for v_node in viking_nodes:
                        v_id = v_node.get('id')
                        print(f"\n--- Node: {v_node.get('title') or v_node.get('name')} (ID: {v_id}) ---")
                        
                        # Get details
                        detail_url = f"https://api.ndla.no/taxonomy/v1/nodes/{v_id}"
                        try:
                            d_resp = requests.get(detail_url)
                            if d_resp.status_code == 200:
                                details = d_resp.json()
                                c_uri = details.get('contentUri')
                                print(f"  Type: {details.get('nodeType')}")
                                print(f"  Content URI: {c_uri}")
                                print(f"  Resource Count: {details.get('resourceCount')}")
                                
                                # If it has a content URI, try to fetch the content
                                if c_uri and c_uri.startswith("urn:article:"):
                                    article_id = c_uri.split(":")[-1]
                                    print(f"  Attempting to fetch content for Article ID: {article_id}")
                                    
                                    # Try resolving the article URN directly via taxonomy
                                    urn_url = f"https://api.ndla.no/taxonomy/v1/nodes/{c_uri}"
                                    print(f"    Trying URN resolution: {urn_url}")
                                    try:
                                        u_resp = requests.get(urn_url)
                                        if u_resp.status_code == 200:
                                            u_data = u_resp.json()
                                            print(f"    SUCCESS! Resolved URN.")
                                            print(f"    Keys: {list(u_data.keys())}")
                                            # Check if there is a 'body' or 'content' here
                                            # or maybe a new 'contentUri' that points elsewhere
                                        else:
                                            print(f"    Failed URN resolution: {u_resp.status_code}")
                                    except Exception as e:
                                        print(f"    Error resolving URN: {e}")

                                    for c_url in content_endpoints:
                                        print(f"    Trying: {c_url}")
                                        try:
                                            c_resp = requests.get(c_url)
                                            if c_resp.status_code == 200:
                                                print(f"    SUCCESS! Content found.")
                                                c_data = c_resp.json()
                                                # print(json.dumps(c_data, indent=2)[:500])
                                                # Check for title/body
                                                print(f"    Title: {c_data.get('title')}")
                                                print(f"    Body length: {len(str(c_data.get('content') or c_data.get('body') or ''))}")
                                                break
                                            else:
                                                print(f"    Failed: {c_resp.status_code}")
                                        except Exception as e:
                                            print(f"    Error: {e}")
                                            
                            else:
                                print(f"  Failed to get details: {d_resp.status_code}")
                        except Exception as e:
                            print(f"  Error getting details: {e}")
                # End of new block
                
                # Define topics list
                topics = [n for n in nodes if n.get('nodeType') == 'TOPIC']
                
                # Inspect a specific topic to see where content lives
                # Using a known topic ID from previous output or just the first one
                if topics:
                    sample_topic = topics[0]
                    t_id = sample_topic.get('id')
                    print(f"\nDeep inspection of Topic ID: {t_id}")
                    
                    # Try fetching the specific node details
                    # Correct endpoint per search results: https://api.ndla.no/taxonomy/v1/nodes/{id}
                    detail_url = f"https://api.ndla.no/taxonomy/v1/nodes/{t_id}"
                    print(f"Fetching details from: {detail_url}")
                    
                    try:
                        d_resp = requests.get(detail_url)
                        if d_resp.status_code == 200:
                            details = d_resp.json()
                            # print(json.dumps(details, indent=2)[:3000])
                            
                            print(f"Keys in details: {list(details.keys())}")
                            print(f"Content URI: {details.get('contentUri')}")
                            print(f"Resource Count: {details.get('resourceCount')}")
                            
                            # If contentUri exists, let's try to fetch it?
                            # Or check 'resources' if available
                            
                        else:
                            print(f"Failed to get details: {d_resp.status_code}")
                    except Exception as e:
                        print(f"Error fetching details: {e}")

            else:
                print(f"Failed to fetch data: {response.status_code}")
                

                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    scrape_ndla_history()
