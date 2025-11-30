from storage import get_db_connection
from sqlalchemy import text

def inspect_keisertiden():
    engine = get_db_connection()
    if not engine:
        return
        
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, subject, topic, title, content FROM learning_materials WHERE title = 'Keisertiden'"))
        rows = result.fetchall()
        
        print(f"Found {len(rows)} entries for 'Keisertiden'.")
        for row in rows:
            print(f"ID: {row[0]}, Subject: {row[1]}, Topic: {row[2]}")
            content = row[4]
            
            # Check for oligarki
            if "oligarki" in content:
                idx = content.find("oligarki")
                start = max(0, idx - 20)
                end = min(len(content), idx + 20)
                print(f"  Snippet around 'oligarki': {repr(content[start:end])}")
            else:
                print("  'oligarki' not found.")
                
            # Check for folketribun
            if "folketribun" in content:
                idx = content.find("folketribun")
                start = max(0, idx - 20)
                end = min(len(content), idx + 20)
                print(f"  Snippet around 'folketribun': {repr(content[start:end])}")
            else:
                print("  'folketribun' not found.")
            print("-" * 20)

if __name__ == "__main__":
    inspect_keisertiden()
