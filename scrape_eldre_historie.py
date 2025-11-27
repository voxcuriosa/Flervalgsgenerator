import requests
import json
import re
from bs4 import BeautifulSoup
from storage import get_db_connection, init_db
from sqlalchemy import text
import time

def get_subtopics(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/nodes"
    print(f"Fetching subtopics from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_resources(node_id):
    url = f"https://api.ndla.no/taxonomy/v1/nodes/{node_id}/resources"
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
    # Find the JSON data
    start_marker = "window.DATA ="
    end_marker = "</script>"
    
    start_idx = html_content.find(start_marker)
    if start_idx == -1:
        return None, None
        
    end_idx = html_content.find(end_marker, start_idx)
    if end_idx == -1:
        return None, None
        
    json_str = html_content[start_idx + len(start_marker):end_idx].strip()
    if json_str.endswith(";"):
        json_str = json_str[:-1]
        
    json_str = json_str.replace("undefined", "null")
    
    try:
        data = json.loads(json_str)
        apollo_state = data.get("apolloState", {})
        
        # Find Article
        article_data = None
        for key, value in apollo_state.items():
            if key.startswith("Article:"):
                article_data = value
                break
        
        if not article_data:
            return None, None
            
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
        
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None, None

def scrape_eldre_historie():
    init_db()
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    eldre_historie_id = "urn:topic:1:00d325d9-d87a-4ef6-9514-7017b0e6a291"
    
    print("Fetching subtopics for 'Eldre historie'...")
    subtopics = get_subtopics(eldre_historie_id)
    print(f"Found {len(subtopics)} subtopics.")
    
    for topic in subtopics:
        topic_name = topic.get('name')
        topic_id = topic.get('id')
        print(f"\n=== Processing Topic: {topic_name} ===")
        
        if topic_name.lower() == "vikingtid" or "vikingtid" in topic_name.lower():
            print("Skipping Vikingtiden (already scraped).")
            continue
            
        # Get resources for this topic
        resources = get_resources(topic_id)
        print(f"Found {len(resources)} resources for {topic_name}.")
        
        for res in resources:
            res_name = res.get('name')
            res_id = res.get('id')
            print(f"  - Processing Resource: {res_name}")
            
            try:
                details = get_node_details(res_id)
                relative_url = details.get('url')
                if not relative_url:
                    print("    No URL found")
                    continue
                    
                full_url = f"https://ndla.no{relative_url}"
                
                # Fetch HTML
                html_response = requests.get(full_url)
                if html_response.status_code != 200:
                    print(f"    Failed to fetch HTML: {html_response.status_code}")
                    continue
                    
                # Extract content
                title, content = extract_content_from_html(html_response.text)
                
                if title and content:
                    print(f"    Extracted: {title} ({len(content)} chars)")
                    
                    # Store in DB
                    with engine.connect() as conn:
                        # Check if exists
                        result = conn.execute(text("SELECT id FROM learning_materials WHERE source_id = :sid"), {"sid": res_id})
                        if result.fetchone():
                            print("    Updating existing record...")
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
                            print("    Inserting new record...")
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
                    print("    Failed to extract content")
                    
            except Exception as e:
                print(f"    Error processing resource {res_id}: {e}")
            
            time.sleep(0.5) # Rate limiting

if __name__ == "__main__":
    scrape_eldre_historie()
