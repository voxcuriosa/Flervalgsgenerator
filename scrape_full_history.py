import requests
import json
import re
from storage import get_db_connection, init_db
from sqlalchemy import text
import time

# Helper functions (reused/adapted)
def extract_node_id_from_url(url):
    print(f"Resolving URL: {url}")
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch URL: {response.status_code}")
            return None
        
        # Regex for UUID in window.DATA
        match = re.search(r'"id":"(urn:topic:1:[a-f0-9-]+)"', response.text)
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

def get_nodes(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/nodes"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching nodes: {e}")
    return []

def get_resources(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/resources"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching resources: {e}")
    return []

def get_node_details(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
        return {}
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
        # intro = article_data.get("htmlIntroduction", "") # Intro often duplicates
        
        content_html = ""
        for key, value in article_data.items():
            if key.startswith("transformedContent"):
                if isinstance(value, dict):
                    content_html += value.get("content", "")
                    
        full_html = f"<div>{content_html}</div>"
        soup = BeautifulSoup(full_html, "html.parser")
        text_content = soup.get_text(separator="\n\n")
        text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()
        
        return title, text_content
    except:
        return None, None

from bs4 import BeautifulSoup

def process_node(node, path_stack, engine):
    node_name = node.get('name')
    node_id = node.get('id')
    
    # Filter out "Om faget"
    if node_name == "Om faget":
        print("Skipping 'Om faget'")
        return

    current_path = path_stack + [node_name]
    path_str = " > ".join(current_path)
    print(f"Processing Node: {path_str}")
    
    # 1. Process Resources in this node
    resources = get_resources(node_id)
    print(f"  Found {len(resources)} resources.")
    
    for res in resources:
        res_name = res.get('name')
        res_id = res.get('id')
        
        # Check if already processed? Maybe update path?
        # Let's scrape content to be sure
        try:
            details = get_node_details(res_id)
            relative_url = details.get('url')
            if not relative_url: continue
                
            full_url = f"https://ndla.no{relative_url}"
            html_response = requests.get(full_url)
            if html_response.status_code != 200: continue
            
            title, content = extract_content_from_html(html_response.text)
            
            if title and content:
                # Store in DB
                with engine.connect() as conn:
                    # Check existence
                    result = conn.execute(text("SELECT id FROM learning_materials WHERE source_id = :sid"), {"sid": res_id})
                    if result.fetchone():
                        # Update
                        conn.execute(text("""
                            UPDATE learning_materials 
                            SET title = :title, content = :content, url = :url, subject = :subject, topic = :topic, path = :path
                            WHERE source_id = :sid
                        """), {
                            "title": title,
                            "content": content,
                            "url": full_url,
                            "subject": "Historie vg2",
                            "topic": node_name, # Immediate parent
                            "path": path_str,   # Full path
                            "sid": res_id
                        })
                    else:
                        # Insert
                        conn.execute(text("""
                            INSERT INTO learning_materials (subject, topic, title, content, url, source_id, path)
                            VALUES (:subject, :topic, :title, :content, :url, :sid, :path)
                        """), {
                            "subject": "Historie vg2",
                            "topic": node_name,
                            "title": title,
                            "content": content,
                            "url": full_url,
                            "sid": res_id,
                            "path": path_str
                        })
                    conn.commit()
                    print(f"    Saved: {title}")
            
            time.sleep(0.1) # Be nice
            
        except Exception as e:
            print(f"    Error processing resource {res_name}: {e}")

    # 2. Process Children Nodes (Recursion)
    children = get_nodes(node_id)
    if children:
        print(f"  Found {len(children)} children nodes. Recursing...")
        for child in children:
            process_node(child, current_path, engine)

def scrape_full_history():
    init_db()
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    # Start URL
    # start_url = "https://ndla.no/f/historie-vg2/905672bc8588"
    # start_node_id = extract_node_id_from_url(start_url)
    
    # Hardcoded Subject ID for "Historie vg2" to ensure we get the root
    start_node_id = "urn:subject:1:ff69c291-6374-4766-80c2-47d5840d8bbf"
    
    if not start_node_id:
        print("Could not resolve start node ID.")
        return
        
    print(f"Start Node ID: {start_node_id}")
    
    # Get top-level children of Historie vg2
    top_nodes = get_nodes(start_node_id)
    print(f"Found {len(top_nodes)} top-level nodes.")
    
    for node in top_nodes:
        # Start recursion from here
        # Path stack starts empty, but effectively "Historie vg2" is implicit subject
        # We can add "Historie vg2" to path if we want, or start with the topic name
        # Let's start with [] so path is "Historiske perioder > Eldre historie" etc.
        process_node(node, [], engine)

if __name__ == "__main__":
    scrape_full_history()
