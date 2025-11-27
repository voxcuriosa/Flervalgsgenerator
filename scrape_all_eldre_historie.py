import requests
import json
import re
from bs4 import BeautifulSoup
from storage import get_db_connection, init_db
from sqlalchemy import text
import time

# Keep track of visited nodes to avoid infinite loops
visited_nodes = set()

def get_nodes(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/nodes"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching nodes for {node_id}: {e}")
    return []

def get_resources(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/resources"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching resources for {node_id}: {e}")
    return []

def get_node_details(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching details for {node_id}: {e}")
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

def process_node(node_id, node_name, engine, depth=0):
    if node_id in visited_nodes:
        return
    visited_nodes.add(node_id)
    
    indent = "  " * depth
    print(f"{indent}Processing Node: {node_name} ({node_id})")
    
    # 1. Get Resources for this node
    resources = get_resources(node_id)
    if resources:
        print(f"{indent}Found {len(resources)} resources.")
        for res in resources:
            res_id = res.get('id')
            res_name = res.get('name')
            
            # Skip if already in DB (optional, but good for speed)
            # Actually, let's just scrape to be sure we update content
            
            try:
                details = get_node_details(res_id)
                relative_url = details.get('url')
                if relative_url:
                    full_url = f"https://ndla.no{relative_url}"
                    html_response = requests.get(full_url)
                    if html_response.status_code == 200:
                        title, content = extract_content_from_html(html_response.text)
                        if title and content:
                            print(f"{indent}- Scraped: {title}")
                            with engine.connect() as conn:
                                result = conn.execute(text("SELECT id FROM learning_materials WHERE source_id = :sid"), {"sid": res_id})
                                if result.fetchone():
                                    conn.execute(text("""
                                        UPDATE learning_materials 
                                        SET title = :title, content = :content, url = :url, subject = :subject, topic = :topic
                                        WHERE source_id = :sid
                                    """), {"title": title, "content": content, "url": full_url, "subject": "Historie vg2", "topic": node_name, "sid": res_id})
                                else:
                                    conn.execute(text("""
                                        INSERT INTO learning_materials (subject, topic, title, content, url, source_id)
                                        VALUES (:subject, :topic, :title, :content, :url, :sid)
                                    """), {"subject": "Historie vg2", "topic": node_name, "title": title, "content": content, "url": full_url, "sid": res_id})
                                conn.commit()
                    time.sleep(0.2)
            except Exception as e:
                print(f"{indent}Error scraping resource {res_name}: {e}")

    # 2. Get Children Nodes (Subtopics)
    children = get_nodes(node_id)
    if children:
        print(f"{indent}Found {len(children)} sub-nodes.")
        for child in children:
            child_name = child.get('name')
            child_id = child.get('id')
            
            # Skip Vikingtiden as requested
            if "vikingtid" in child_name.lower():
                print(f"{indent}Skipping {child_name}")
                continue
                
            process_node(child_id, child_name, engine, depth + 1)

def scrape_all():
    init_db()
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    eldre_historie_id = "urn:topic:1:00d325d9-d87a-4ef6-9514-7017b0e6a291"
    process_node(eldre_historie_id, "Eldre historie", engine)

if __name__ == "__main__":
    scrape_all()
