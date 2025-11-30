import requests
import re
import json

def extract_node_id_from_url(url):
    print(f"Resolving URL: {url}")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch URL: {response.status_code}")
            return None
        
        # Regex for UUID in window.DATA
        match = re.search(r'"id":"(urn:topic:[a-f0-9-]+)"', response.text)
        if match:
            return match.group(1)
            
        # Fallback: Parse window.DATA
        start_marker = "window.DATA ="
        end_marker = "</script>"
        start_idx = response.text.find(start_marker)
        if start_idx != -1:
            end_idx = response.text.find(end_marker, start_idx)
            if end_idx != -1:
                json_str = response.text[start_idx + len(start_marker):end_idx].strip()
                if json_str.endswith(";"): json_str = json_str[:-1]
                json_str = json_str.replace("undefined", "null")
                data = json.loads(json_str)
                if 'pageContext' in data and 'nodeId' in data['pageContext']:
                    return data['pageContext']['nodeId']
    except Exception as e:
        print(f"Error resolving URL: {e}")
    return None

url = "https://ndla.no/f/historie-pb/1e9649854f03"
node_id = extract_node_id_from_url(url)
print(f"Node ID: {node_id}")
