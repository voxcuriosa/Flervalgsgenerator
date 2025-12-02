import requests
import re
import json

urls = {
    "Kroppsøving (vg2)": "https://ndla.no/f/kroppsoving-vg2/ef3ac9038dd8",
    "Matematikk 2P": "https://ndla.no/f/matematikk-2p/36bbf8f78d78",
    "Norsk (SF vg2)": "https://ndla.no/f/norsk-sf-vg2/c86dc51f59f1",
    "Matematikk R1": "https://ndla.no/f/matematikk-r1/17014b16d4f9",
    "Matematikk S1": "https://ndla.no/f/matematikk-s1/8b9a33345c01",
    "Engelsk 1": "https://ndla.no/f/engelsk-1/c06d3af5cb02",
    "Kroppsøving (vg3)": "https://ndla.no/f/kroppsoving-vg3/935930a34178",
    "Norsk (SF vg3)": "https://ndla.no/f/norsk-sf-vg3/61e7e4cc53e5",
    "Religion og etikk": "https://ndla.no/f/religion-og-etikk/7d0fb836fb09",
    "Matematikk R2": "https://ndla.no/f/matematikk-r2/efa1e27bd31b",
    "Matematikk S2": "https://ndla.no/f/matematikk-s2/9d0d3bb13246",
    "Engelsk 2": "https://ndla.no/f/engelsk-2/181a81f71d0b",
    "Mediesamfunnet 1": "https://ndla.no/f/mediesamfunnet-1/54d418003b61",
    "Medieuttrykk 1": "https://ndla.no/f/medieuttrykk-1/a3f7f15a28a1",
    "Mediesamfunnet 2": "https://ndla.no/f/mediesamfunnet-2/040c7428ca64",
    "Medieuttrykk 2": "https://ndla.no/f/medieuttrykk-2/312cb3adaa3d",
    "Mediesamfunnet 3": "https://ndla.no/f/mediesamfunnet-3/46dde538daae",
    "Medieuttrykk 3": "https://ndla.no/f/medieuttrykk-3/47d64a284b6a"
}

def get_id(url):
    try:
        response = requests.get(url)
        match = re.search(r'"id":"(urn:subject:[^"]+)"', response.text)
        if match:
            return match.group(1)
        # Try finding any urn:subject
        match = re.search(r'(urn:subject:[a-f0-9-]+)', response.text)
        if match:
             return match.group(1)
        # Try window.DATA approach
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
        return f"Error: {e}"
    return "Not Found"

for name, url in urls.items():
    print(f'    "{name}": "{get_id(url)}",')
