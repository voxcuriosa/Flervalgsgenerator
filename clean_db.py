from storage import get_db_connection
from sqlalchemy import text

def clean_db():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect")
        return
        
    with engine.connect() as conn:
        # Delete items where topic is 'Om faget' or path contains 'Om faget'
        conn.execute(text("DELETE FROM learning_materials WHERE topic = 'Om faget' OR path LIKE '%Om faget%'"))
        conn.commit()
        print("Deleted 'Om faget' entries.")

if __name__ == "__main__":
    clean_db()
