import requests
import json
import re
from bs4 import BeautifulSoup
from storage import get_db_connection, init_db
from sqlalchemy import text
import time

def extract_node_id_from_url(url):
    print(f"Resolving URL: {url}")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch URL: {response.status_code}")
            return None
            
        # Look for the ID in the HTML content
        # It's usually in window.DATA or similar
        # Or we can look for the canonical link or meta tags
        
        # Method 1: Regex for UUID in window.DATA
        match = re.search(r'"id":"(urn:topic:1:[a-f0-9-]+)"', response.text)
        if match:
            return match.group(1)
            
        # Method 2: Look for the short ID in the URL and try to find it in the page source
        # The URL ends with 58fcf9d8bb. 
        
        # Let's try parsing the window.DATA JSON
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
                
                # The main node ID is often in 'pageContext' or 'apolloState'
                # Let's look for the current node
                if 'pageContext' in data and 'nodeId' in data['pageContext']:
                    return data['pageContext']['nodeId']
                    
    except Exception as e:
        print(f"Error resolving URL: {e}")
    return None

def get_resources(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/resources"
    print(f"Fetching resources from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_node_details(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def extract_content_from_html(html_content):
    start_marker = "window.DATA ="
    end_marker = "</script>"
    
    start_idx = html_content.find(start_marker)
    if start_idx == -1: return None, None
        
    end_idx = html_content.find(end_marker, start_idx)
    if end_idx == -1: return None, None
        
    json_str = html_content[start_idx + len(start_marker):end_idx].strip()
    if json_str.endswith(";"): json_str = json_str[:-1]
    json_str = json_str.replace("undefined", "null")
    
    try:
        data = json.loads(json_str)
        apollo_state = data.get("apolloState", {})
        
        article_data = None
        for key, value in apollo_state.items():
            if key.startswith("Article:"):
                article_data = value
                break
        
        if not article_data: return None, None
            
        title = article_data.get("title") or article_data.get("htmlTitle")
        intro = article_data.get("htmlIntroduction", "")
        
        content_html = ""
        for key, value in article_data.items():
            if key.startswith("transformedContent"):
                if isinstance(value, dict):
                    content_html += value.get("content", "")
                    
        full_html = f"<div>{intro}</div>{content_html}"
        soup = BeautifulSoup(full_html, "html.parser")
        text_content = soup.get_text(separator="\n\n")
        text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()
        
        return title, text_content
    except:
        return None, None

def get_nodes(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/nodes"
    print(f"Fetching children from: {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching nodes: {e}")
    return []

def scrape_perioder():
    init_db()
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    target_url = "https://ndla.no/e/historie-vg2/a-dele-i-perioder/58fcf9d8bb"
    node_id = extract_node_id_from_url(target_url)
    
    if not node_id:
        print("Could not find Node ID.")
        return

    print(f"Found Node ID: {node_id}")
    topic_name = "Å dele i perioder"
    
    # 1. Try Resources
    resources = get_resources(node_id)
    print(f"Found {len(resources)} direct resources.")
    
    # 2. Try Children if no resources or just to be thorough
    children = get_nodes(node_id)
    print(f"Found {len(children)} children nodes.")
    
    # Combine list to process
    items_to_process = []
    
    # Add direct resources
    for res in resources:
        items_to_process.append(res)
        
    # Add resources from children (simplified 1-level depth for now)
    for child in children:
        print(f"Checking child: {child.get('name')}")
        child_resources = get_resources(child.get('id'))
        print(f"  Found {len(child_resources)} resources in child.")
        items_to_process.extend(child_resources)
        
    print(f"Total items to process: {len(items_to_process)}")
    
    for res in items_to_process:
        res_name = res.get('name')
        res_id = res.get('id')
        print(f"Processing: {res_name}")
        
        try:
            details = get_node_details(res_id)
            relative_url = details.get('url')
            if not relative_url:
                print("  No URL found")
                continue
                
            full_url = f"https://ndla.no{relative_url}"
            
            html_response = requests.get(full_url)
            if html_response.status_code != 200:
                print(f"  Failed to fetch HTML: {html_response.status_code}")
                continue
                
            title, content = extract_content_from_html(html_response.text)
            
            if title and content:
                print(f"  Extracted: {title} ({len(content)} chars)")
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT id FROM learning_materials WHERE source_id = :sid"), {"sid": res_id})
                    if result.fetchone():
                        conn.execute(text("""
                            UPDATE learning_materials 
                            SET title = :title, content = :content, url = :url, subject = :subject, topic = :topic
                            WHERE source_id = :sid
                        """), {
                            "title": title,
                            "content": content,
                            "url": full_url,
                            "subject": "Historie vg2",
                            "topic": topic_name,
                            "sid": res_id
                        })
                    else:
                        conn.execute(text("""
                            INSERT INTO learning_materials (subject, topic, title, content, url, source_id)
                            VALUES (:subject, :topic, :title, :content, :url, :sid)
                        """), {
                            "subject": "Historie vg2",
                            "topic": topic_name,
                            "title": title,
                            "content": content,
                            "url": full_url,
                            "sid": res_id
                        })
                    conn.commit()
            else:
                print("  Failed to extract content")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    scrape_perioder()
