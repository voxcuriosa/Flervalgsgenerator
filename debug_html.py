import requests
import json
from bs4 import BeautifulSoup
import re

def debug_html():
    url = "https://ndla.no/r/historie-vg2/keisertiden/b1b0420b52"
    print(f"Fetching {url}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed: {response.status_code}")
        return

    html_content = response.text
    
    # Extract JSON data
    start_marker = "window.DATA ="
    end_marker = "</script>"
    
    start_idx = html_content.find(start_marker)
    if start_idx == -1: 
        print("Start marker not found")
        return
        
    end_idx = html_content.find(end_marker, start_idx)
    if end_idx == -1: 
        print("End marker not found")
        return
        
    json_str = html_content[start_idx + len(start_marker):end_idx].strip()
    if json_str.endswith(";"): json_str = json_str[:-1]
    json_str = json_str.replace("undefined", "null")
    
    data = json.loads(json_str)
    apollo_state = data.get("apolloState", {})
    
    article_data = None
    for key, value in apollo_state.items():
        if key.startswith("Article:"):
            article_data = value
            break
            
    if not article_data:
        print("Article data not found")
        return
        
    content_html = ""
    for key, value in article_data.items():
        if key.startswith("transformedContent"):
            if isinstance(value, dict):
                content_html += value.get("content", "")
                
    full_html = f"<div>{content_html}</div>"
    
    # Print raw HTML around "oligarki"
    idx = full_html.find("oligarki")
    if idx != -1:
        print("\nRaw HTML around 'oligarki':")
        print(full_html[max(0, idx-100):min(len(full_html), idx+100)])
    else:
        print("'oligarki' not found in raw HTML")

    # Print raw HTML around "folketribun"
    idx = full_html.find("folketribun")
    if idx != -1:
        print("\nRaw HTML around 'folketribun':")
        print(full_html[max(0, idx-100):min(len(full_html), idx+100)])
    else:
        print("'folketribun' not found in raw HTML")
        
    # Test current extraction logic
    soup = BeautifulSoup(full_html, "html.parser")
    
    # Unwrap inline tags
    for tag_name in ["em", "i", "strong", "b", "a", "span", "code"]:
        for tag in soup.find_all(tag_name):
            tag.unwrap()
            
    text_content = soup.get_text(separator="\n\n")
    text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()
    
    print("\nExtracted Text around 'oligarki':")
    idx = text_content.find("oligarki")
    if idx != -1:
        print(repr(text_content[max(0, idx-50):min(len(text_content), idx+50)]))
        
    print("\nExtracted Text around 'folketribun':")
    idx = text_content.find("folketribun")
    if idx != -1:
        print(repr(text_content[max(0, idx-50):min(len(text_content), idx+50)]))

if __name__ == "__main__":
    debug_html()
