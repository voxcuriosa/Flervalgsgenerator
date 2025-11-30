from storage import get_db_connection
from sqlalchemy import text

def verify_cleanup():
    engine = get_db_connection()
    if not engine:
        return
        
    with engine.connect() as conn:
        # Check for the specific example mentioned by the user
        result = conn.execute(text("SELECT content FROM learning_materials WHERE content LIKE '%folketribun%' LIMIT 1"))
        row = result.fetchone()
        if row:
            print("Found content with 'folketribun':")
            # Print a snippet around the word
            content = row[0]
            idx = content.find("folketribun")
            start = max(0, idx - 50)
            end = min(len(content), idx + 50)
            print(f"...{content[start:end]}...")
        else:
            print("Could not find 'folketribun'")

if __name__ == "__main__":
    verify_cleanup()
