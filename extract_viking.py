import json
import re
from bs4 import BeautifulSoup
from storage import get_db_connection, init_db
from sqlalchemy import text

# Initialize DB
init_db()

# Get engine
engine = get_db_connection()

def extract_and_store():
    # Read the HTML file
    with open("viking.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # Find the JSON data
    # Looking for: window.DATA = {...}
    start_marker = "window.DATA ="
    end_marker = "</script>"
    
    start_idx = html_content.find(start_marker)
    if start_idx == -1:
        print("Could not find window.DATA in HTML")
        return
        
    end_idx = html_content.find(end_marker, start_idx)
    if end_idx == -1:
        print("Could not find end of script tag")
        return
        
    # Extract the content
    json_str = html_content[start_idx + len(start_marker):end_idx].strip()
    
    # Remove trailing semicolon if present
    if json_str.endswith(";"):
        json_str = json_str[:-1]
        
    # Fix JS specific values that are not valid JSON
    json_str = json_str.replace("undefined", "null")
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return

    # Navigate to article data
    apollo_state = data.get("apolloState", {})
    
    # Find the Article object
    article_data = None
    article_id = None
    
    for key, value in apollo_state.items():
        if key.startswith("Article:"):
            article_data = value
            article_id = key
            break
            
    if not article_data:
        print("Could not find Article data in JSON")
        return

    # List all Nodes and Articles to find the resources
    print("\n--- All Nodes in JSON ---")
    for key, value in apollo_state.items():
        if key.startswith("Node:"):
            name = value.get("name") or value.get("title")
            print(f"Key: {key}, Name: {name}, Type: {value.get('nodeType')}")
            
    print("\n--- All Articles in JSON ---")
    for key, value in apollo_state.items():
        if key.startswith("Article:"):
            title = value.get("title") or value.get("htmlTitle")
            print(f"Key: {key}, Title: {title}")


    # Define full_html to avoid NameError if we skipped the previous block
    full_html = ""
    
    # Extract fields from article_data if available
    if article_data:
        title = article_data.get("title") or article_data.get("htmlTitle")
        intro = article_data.get("htmlIntroduction", "")
        
        content_html = ""
        for key, value in article_data.items():
            if key.startswith("transformedContent"):
                if isinstance(value, dict):
                    content_html += value.get("content", "")
        
        full_html = f"<div>{intro}</div>{content_html}"
    
    # Clean HTML to text
    soup = BeautifulSoup(full_html, "html.parser")
    text_content = soup.get_text(separator="\n\n")
    
    # Clean up excessive newlines
    text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()
    
    print(f"Title: {title}")
    print(f"Extracted text length: {len(text_content)}")
    print(f"Preview: {text_content[:200]}...")
    
    # Store in DB
    url = "https://ndla.no/e/historie-vg2/vikingtid/61e04b2fc0"
    subject = "Historie vg2"
    topic = "Vikingtiden"
    
    try:
        with engine.connect() as conn:
            # Check if exists
            result = conn.execute(text("SELECT id FROM learning_materials WHERE source_id = :sid"), {"sid": article_id})
            if result.fetchone():
                print("Article already exists in DB. Updating...")
                conn.execute(text("""
                    UPDATE learning_materials 
                    SET title = :title, content = :content, url = :url, subject = :subject, topic = :topic
                    WHERE source_id = :sid
                """), {
                    "title": title,
                    "content": text_content,
                    "url": url,
                    "subject": subject,
                    "topic": topic,
                    "sid": article_id
                })
            else:
                print("Inserting new article...")
                conn.execute(text("""
                    INSERT INTO learning_materials (subject, topic, title, content, url, source_id)
                    VALUES (:subject, :topic, :title, :content, :url, :sid)
                """), {
                    "subject": subject,
                    "topic": topic,
                    "title": title,
                    "content": text_content,
                    "url": url,
                    "sid": article_id
                })
            conn.commit()
            print("Successfully stored in database!")
            
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    extract_and_store()
