from storage import get_db_connection
from sqlalchemy import text

def get_keisertiden_url():
    engine = get_db_connection()
    if not engine:
        return
        
    with engine.connect() as conn:
        result = conn.execute(text("SELECT url FROM learning_materials WHERE title = 'Keisertiden' LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"URL: {row[0]}")
        else:
            print("Keisertiden not found")

if __name__ == "__main__":
    get_keisertiden_url()
