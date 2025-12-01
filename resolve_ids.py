import requests
import re
import json

urls = {
    "Norsk (PB)": "https://ndla.no/f/norsk-pb/2157a7763414",
    "Geografi": "https://ndla.no/f/geografi/b6b445755675",
    "Matematikk 1P": "https://ndla.no/f/matematikk-1p/08bed615ef2d",
    "Matematikk 1T": "https://ndla.no/f/matematikk-1t/be2ae5a11bba",
    "Norsk (SF vg1)": "https://ndla.no/f/norsk-sf-vg1/4a16fb6cacbc",
    "Norsk kort botid (SF vg1)": "https://ndla.no/f/norsk-kort-botid-sf-vg1/ddd74d2d3386",
    "Tysk 1": "https://ndla.no/f/tysk-1/6421475f0630",
    "Tysk 2": "https://ndla.no/f/tysk-2/26ecb08cfc89"
}

def resolve_id(name, url):
    print(f"Resolving {name}...")
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"  Failed to fetch page: {resp.status_code}")
            return None
            
        match = re.search(r'"id":"(urn:subject:[^"]+)"', resp.text)
        if match:
            return match.group(1)
            
        match_topic = re.search(r'"id":"(urn:topic:[^"]+)"', resp.text)
        if match_topic:
            return match_topic.group(1)
            
        print("  Could not find ID in HTML.")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

results = {}
for name, url in urls.items():
    res = resolve_id(name, url)
    if res:
        print(f"  FOUND: {res}")
        results[name] = res
    else:
        print("  FAILED")

print("\n--- RESULTS ---")
for k, v in results.items():
    print(f'    elif subject_name == "{k}":')
    print(f'        root_node_id = "{v}"')
