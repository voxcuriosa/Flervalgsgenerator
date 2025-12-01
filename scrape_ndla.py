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
        
        # 1. Unwrap inline tags
        for tag_name in ["em", "i", "strong", "b", "a", "span", "code", "u", "mark", "small"]:
            for tag in soup.find_all(tag_name):
                tag.unwrap()
                
        # 2. Handle breaks
        for br in soup.find_all("br"):
            br.replace_with("\n")
            
        # 3. Handle block elements - ensure they end with newline
        # We append a newline to the text of block elements if not present
        # Actually, simpler: insert a newline string after block elements
        for tag_name in ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "section", "article"]:
            for tag in soup.find_all(tag_name):
                tag.insert_after("\n\n")
                
        # 4. Get text with empty separator (relying on our manual newlines)
        text_content = soup.get_text(separator="")
        
        # 5. Cleanup
        text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()
        
        return title, text_content
    except:
        return None, None

def process_node(node, path_stack, engine, subject_name):
    node_name = node.get('name')
    node_id = node.get('id')
    
    # Filter out "Om faget" - ENABLED AGAIN per user request
    # Filter out "Om faget" - ONLY for specific subjects per user request
    # Drop for: Geografi, Matematikk 1P, Matematikk 1T
    # Keep for: Norsk (PB), Norsk (SF vg1), Norsk kort botid (SF vg1), Tysk 1, Tysk 2
    subjects_to_skip_om_faget = ["Geografi", "Matematikk 1P", "Matematikk 1T"]
    
    if node_name == "Om faget" and subject_name in subjects_to_skip_om_faget:
        print(f"Skipping 'Om faget' for {subject_name}")
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
                # Suffix source_id with subject to allow same content in multiple subjects
                # This bypasses the UNIQUE(source_id) constraint
                db_source_id = f"{res_id}#{subject_name}"
                
                # Store in DB
                with engine.connect() as conn:
                    # Check existence for this specific subject (using suffixed ID)
                    result = conn.execute(text("SELECT id FROM learning_materials WHERE source_id = :sid"), {"sid": db_source_id})
                    if result.fetchone():
                        # Update
                        conn.execute(text("""
                            UPDATE learning_materials 
                            SET title = :title, content = :content, url = :url, topic = :topic, path = :path
                            WHERE source_id = :sid
                        """), {
                            "title": title,
                            "content": content,
                            "url": full_url,
                            "topic": node_name, # Immediate parent
                            "path": path_str,   # Full path
                            "sid": db_source_id
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
                            "sid": db_source_id,
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

def get_subject_topics(subject_name):
    """
    Returns a list of top-level topics for a subject.
    Returns: [{'name': 'Topic Name', 'id': 'urn:topic:...'}]
    """
    root_node_id = None
    if subject_name == "Historie vg3":
        root_node_id = "urn:subject:cc109c51-a083-413b-b497-7f80a0569a92"
    elif subject_name == "Historie vg2":
        root_node_id = "urn:subject:1:ff69c291-6374-4766-80c2-47d5840d8bbf"
    elif subject_name == "Sosiologi og sosialantropologi":
        root_node_id = "urn:subject:1:fb6ad516-0108-4059-acc3-3c5f13f49368"
    elif subject_name == "Historie (PB)":
        root_node_id = "urn:subject:846a7552-ea6c-4174-89a4-85d6ba48c96e"
    elif subject_name == "Samfunnskunnskap":
        root_node_id = "urn:subject:1:470720f9-6b03-40cb-ab58-e3e130803578"
    elif subject_name == "Norsk (PB)":
        root_node_id = "urn:subject:af91136f-7da8-4cf1-b0ba-0ea6acdf1489"
    elif subject_name == "Geografi":
        root_node_id = "urn:subject:f041dc02-55f3-4f01-a9c9-962bef5a1eff"
    elif subject_name == "Matematikk 1P":
        root_node_id = "urn:subject:1:a3c1b65a-c41f-4879-b650-32a13fe1801b"
    elif subject_name == "Matematikk 1T":
        root_node_id = "urn:subject:1:8bfd0a97-d456-448d-8b5f-3bc49e445b37"
    elif subject_name == "Norsk (SF vg1)":
        root_node_id = "urn:subject:1:605d33e0-1695-4540-9255-fc5e612e996f"
    elif subject_name == "Norsk kort botid (SF vg1)":
        root_node_id = "urn:subject:c02a4ac1-3121-4985-b7b2-cf158502a960"
    elif subject_name == "Tysk 1":
        root_node_id = "urn:subject:1:1a05c6c7-121e-49e2-933c-580da74afe1a"
    elif subject_name == "Tysk 2":
        root_node_id = "urn:subject:1:ec288dfb-4768-4f82-8387-fe2d73fff1e1"
    
    if not root_node_id:
        return []
        
    try:
        # Get root node details
        root_details = get_node_details(root_node_id)
        if not root_details:
            return []
            
        # Get children
        children = get_nodes(root_node_id)
        
        topics = []
        for child in children:
            name = child.get('name', '').strip()
            # Filter out "Om faget" (robust check) - ENABLED AGAIN
            # if name.lower() == "om faget":
            #     continue
                
            # We only want topics, not resources (though at this level they should be topics)
            # Filter out "Diverse" if we want, or keep it.
            topic_data = {
                'name': name,
                'id': child.get('id'),
                'children': []
            }
            
            # Fetch subtopics (Level 2)
            try:
                sub_children = get_nodes(child.get('id'))
                for sub in sub_children:
                    sub_name = sub.get('name', '').strip()
                    # if sub_name.lower() == "om faget":
                    #     continue
                        
                    topic_data['children'].append({
                        'name': sub_name,
                        'id': sub.get('id')
                    })
            except:
                pass # Ignore errors for subtopics
                
            topics.append(topic_data)
            
        return topics
    except Exception as e:
        print(f"Error fetching topics: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape NDLA subject content.")
    parser.add_argument("subject", help="Name of the subject (e.g., 'Historie vg3')")
    parser.add_argument("url", help="Start URL or Node ID")
    
    args = parser.parse_args()
    
    scrape_subject(args.subject, args.url)
