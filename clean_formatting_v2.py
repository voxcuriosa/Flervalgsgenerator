from storage import get_db_connection
from sqlalchemy import text
import re

def clean_formatting_v2():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect")
        return
        
    print("Fetching all content...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, content FROM learning_materials"))
        rows = result.fetchall()
        
    print(f"Found {len(rows)} rows. Checking for formatting issues...")
    
    updates = []
    
    # Regex to find " \n\n word" where word is lowercase or starts with comma
    # We want to replace "\n\n" with " " if it looks like it split a sentence.
    
    # Pattern:
    # (non-sentence-ender) + (optional space) + \n+ + (optional space) + (lowercase or comma)
    
    # We will use a function to process the text to be safer
    
    for row in rows:
        row_id = row[0]
        content = row[1]
        if not content: continue
        
        original_content = content
        
        # Split by double newlines
        parts = re.split(r'(\n{2,})', content)
        
        new_parts = []
        for i in range(len(parts)):
            part = parts[i]
            
            # If this is a newline separator
            if re.match(r'\n{2,}', part):
                # Check context
                prev_part = parts[i-1] if i > 0 else ""
                next_part = parts[i+1] if i < len(parts)-1 else ""
                
                # Clean whitespace for checking
                prev_clean = prev_part.strip()
                next_clean = next_part.strip()
                
                should_merge = False
                
                if prev_clean and next_clean:
                    last_char = prev_clean[-1]
                    first_char = next_clean[0]
                    
                    # Heuristic: Merge if previous doesn't end with .!? and next starts with lowercase or ,
                    if last_char not in ".!?:":
                        if first_char.islower() or first_char == ",":
                            should_merge = True
                            
                    # Also handle the specific case "eller \n\n oligarki"
                    # "eller" doesn't end in punct. "oligarki" is lower.
                    
                    # Handle "til \n\n folketribun"
                    # "til" no punct. "folketribun" lower.
                    
                if should_merge:
                    new_parts.append(" ")
                else:
                    new_parts.append(part)
            else:
                new_parts.append(part)
                
        new_content = "".join(new_parts)
        
        # Cleanup potential double spaces
        new_content = re.sub(r' {2,}', ' ', new_content)
        
        if new_content != original_content:
            updates.append({"id": row_id, "content": new_content})

    print(f"Found {len(updates)} rows to update.")
    
    if updates:
        with engine.connect() as conn:
            for update in updates:
                conn.execute(text("UPDATE learning_materials SET content = :content WHERE id = :id"), update)
            conn.commit()
        print("Database updated.")

if __name__ == "__main__":
    clean_formatting_v2()
