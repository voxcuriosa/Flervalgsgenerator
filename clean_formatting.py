from storage import get_db_connection
from sqlalchemy import text
import re

def clean_formatting():
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
    for row in rows:
        row_id = row[0]
        content = row[1]
        
        if not content:
            continue
            
        # Fix: Remove excessive newlines around what looks like previously inline text
        # Pattern: newline(s) + word + newline(s) -> space + word + space
        # This is tricky because we don't want to merge paragraphs.
        # But the user example showed: " ... gjorde seg til \n\n folketribun \n\n , den som ..."
        
        # A safer approach might be to target specific patterns or just general cleanup of
        # " \n\n word \n\n " where word is short?
        # Or maybe just collapse multiple newlines if they are surrounded by text that flows?
        
        # Let's try to fix the specific example pattern:
        # "text \n\n word \n\n text" -> "text word text"
        
        # Actually, the user wants to fix "endel orde som er formatert veldig rart med mange mellomrom".
        # The example: "Han gjorde seg til \n\n folketribun \n\n , den som..."
        
        # Regex to find a word surrounded by double newlines
        # We want to replace "\n\n word \n\n" with " word "
        
        # Let's try a more aggressive cleanup for this specific issue.
        # We can look for lines that don't end with punctuation and are followed by a line that starts with lowercase?
        
        # Better: The issue is likely caused by the previous scraper logic.
        # We can try to re-process the content if we assume the structure.
        # But we don't have the HTML anymore.
        
        # Heuristic:
        # If we see "\n\n" followed by a word (no punctuation) followed by "\n\n", it's likely an unwrapped inline tag.
        # Exception: Headings? Headings usually don't have punctuation, but they are usually followed by a new paragraph.
        
        # Let's try to replace "\n\n" with " " if the preceding line does NOT end with sentence-ending punctuation (.!?)
        # AND the following line does NOT start with an uppercase letter?
        # This is risky for bullet points.
        
        # Let's look at the specific example:
        # "...til\n\nfolketribun\n\n, den..."
        # "...til" (no punct) -> "\n\n" -> "folketribun" (lowercase) -> "\n\n" -> ", den" (starts with comma)
        
        new_content = content
        
        # Case 1: Word surrounded by newlines, preceded by non-punctuation, followed by punctuation or lowercase
        # This is hard to regex perfectly.
        
        # Let's try a simpler approach:
        # Collapse "\n\n" to " " if it seems to be inside a sentence.
        # Inside a sentence means: Preceding char is not .!? and Following char is lowercase or punctuation.
        
        def replacer(match):
            # match.group(0) is the newline sequence
            # We need lookbehind/lookahead logic, but re.sub doesn't support variable width lookbehind easily.
            return " "

        # Pattern: (?<![.!?])\n+(?=[a-z,])
        # Negative lookbehind for sentence enders.
        # Match newlines.
        # Positive lookahead for lowercase or comma.
        
        # Note: Python's re module requires fixed width lookbehind.
        # So we can't do (?<![.!?]) directly if we want to match variable newlines?
        # Actually (?<![.!?]) is fixed width (1 char).
        
        # Try to fix: "... til \n\n folketribun \n\n , den ..."
        # 1. "... til" -> no punct.
        # 2. "\n\n"
        # 3. "folketribun" -> starts with lowercase.
        # Match! Replace with space.
        # Result: "... til folketribun \n\n , den ..."
        
        # Next: "folketribun" -> no punct.
        # "\n\n"
        # ", den" -> starts with comma.
        # Match! Replace with space.
        # Result: "... til folketribun , den ..."
        
        # This looks promising.
        
        # Regex:
        # (?<=[^.!?:])\s*\n\s*(?=[a-z,])
        # Lookbehind: Preceded by a char that is NOT . ! ? :
        # Match: Whitespace including newlines
        # Lookahead: Followed by lowercase letter or comma
        
        cleaned = re.sub(r'(?<=[^.!?:])\s*\n\s*(?=[a-z,])', ' ', new_content)
        
        # Also handle the case where the inline word was at the start/end of the weird block?
        # The example had "folketribun" on its own line.
        
        if cleaned != content:
            updates.append({"id": row_id, "content": cleaned})

    print(f"Found {len(updates)} rows to update.")
    
    if updates:
        with engine.connect() as conn:
            for update in updates:
                conn.execute(text("UPDATE learning_materials SET content = :content WHERE id = :id"), update)
            conn.commit()
        print("Database updated.")

if __name__ == "__main__":
    clean_formatting()
