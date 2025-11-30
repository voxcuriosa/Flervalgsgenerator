from storage import get_db_connection
from sqlalchemy import text

def check_subject():
    engine = get_db_connection()
    if not engine:
        return
        
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM learning_materials WHERE subject = 'Historie (PB)'"))
        count = result.scalar()
        print(f"Entries for 'Historie (PB)': {count}")
        
        # Check distinct subjects
        result = conn.execute(text("SELECT DISTINCT subject FROM learning_materials"))
        subjects = [row[0] for row in result.fetchall()]
        print(f"Subjects in DB: {subjects}")

if __name__ == "__main__":
    check_subject()
