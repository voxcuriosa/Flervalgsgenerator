from storage import get_db_connection
from sqlalchemy import text

def inspect_sosiologi():
    engine = get_db_connection()
    if not engine:
        print("No engine")
        return

    query = text("SELECT title, content FROM learning_materials WHERE subject = 'Sosiologi og sosialantropologi' LIMIT 1")
    with engine.connect() as conn:
        result = conn.execute(query).fetchone()
        if result:
            print(f"Title: {result.title}")
            print("-" * 20)
            print(result.content)
            print("-" * 20)
        else:
            print("No Sosiologi content found.")

if __name__ == "__main__":
    inspect_sosiologi()
