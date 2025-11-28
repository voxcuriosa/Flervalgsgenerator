import requests
import json
import re
import time
import argparse
from bs4 import BeautifulSoup
from sqlalchemy import text
from storage import get_db_connection, init_db

# --- Helper Functions ---

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

def process_node(node, path_stack, engine, subject_name):
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
                            "subject": subject_name,
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
                            "subject": subject_name,
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
            process_node(child, current_path, engine, subject_name)

def scrape_subject(subject_name, start_url_or_id):
    init_db()
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    if start_url_or_id.startswith("http"):
        start_node_id = extract_node_id_from_url(start_url_or_id)
    else:
        start_node_id = start_url_or_id
    
    if not start_node_id:
        print("Could not resolve start node ID.")
        return
        
    print(f"Start Node ID: {start_node_id}")
    
    # Get top-level children
    top_nodes = get_nodes(start_node_id)
    print(f"Found {len(top_nodes)} top-level nodes.")
    
    for node in top_nodes:
        process_node(node, [], engine, subject_name)

def update_topic(subject_name, topic_name, node_id):
    """
    Scrapes a specific topic and updates the database.
    This is designed to be called from the Streamlit app.
    """
    print(f"Updating topic: {topic_name} ({node_id})")
    
    # We need to create a new DB connection here since this might run in a thread
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return False

    try:
        # Get the node details to find children
        # If node_id is a URL, resolve it
        if node_id.startswith("http"):
            real_node_id = extract_node_id_from_url(node_id)
        else:
            real_node_id = node_id
            
        if not real_node_id:
            print("Could not resolve node ID")
            return False
            
        # Process this node and its children
        # We need to reconstruct the path. Since we are updating a specific topic,
        # we can assume the path starts with the topic name.
        # OR we can try to fetch the parent path? 
        # For simplicity, let's just use the topic name as the root of this update.
        # But wait, if we are updating "Nyere historie", it is under "Historiske perioder".
        # The process_node function builds the path.
        
        # Let's fetch the node info to get its name
        details = get_node_details(real_node_id)
        actual_name = details.get('name', topic_name)
        
        # We need to pass a path stack. 
        # If we don't know the parent, maybe we can just use [actual_name]?
        # But then it won't match the full hierarchy if we scraped from root.
        # Ideally we should look up the existing path in the DB if possible?
        # Or just accept that updating a sub-topic might have a partial path if run in isolation?
        # Actually, process_node appends to path_stack.
        
        # Let's try to find the path from the DB for this topic if it exists
        with engine.connect() as conn:
            result = conn.execute(text("SELECT path FROM learning_materials WHERE topic = :topic AND subject = :subject LIMIT 1"), {"topic": actual_name, "subject": subject_name})
            row = result.fetchone()
            if row and row[0]:
                # e.g. "Historiske perioder > Nyere historie"
                # If we are processing "Nyere historie", the path stack passed to it should be the PARENT path.
                full_path = row[0]
                if " > " in full_path:
                    parent_path_str = full_path.rsplit(" > ", 1)[0]
                    path_stack = parent_path_str.split(" > ")
                else:
                    path_stack = [] # It's a root node
            else:
                # Fallback
                path_stack = [] 

        # Now process
        # Note: process_node expects the node dict, not just ID
        node_data = get_node_details(real_node_id)
        if not node_data:
            node_data = {"id": real_node_id, "name": actual_name}
            
        process_node(node_data, path_stack, engine, subject_name)
        return True
        
    except Exception as e:
        print(f"Error updating topic: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape NDLA subject content.")
    parser.add_argument("subject", help="Name of the subject (e.g., 'Historie vg3')")
    parser.add_argument("url", help="Start URL or Node ID")
    
    args = parser.parse_args()
    
    scrape_subject(args.subject, args.url)
