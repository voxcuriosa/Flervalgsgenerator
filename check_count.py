from storage import get_db_connection
from sqlalchemy import text

def check_count():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect")
        return
    with engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*) FROM learning_materials")).scalar()
        print(f"Total articles: {res}")

if __name__ == "__main__":
    check_count()
