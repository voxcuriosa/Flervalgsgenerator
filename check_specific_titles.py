from storage import get_db_connection
from sqlalchemy import text
import pandas as pd

def check_titles():
    conn = get_db_connection()
    if conn:
        try:
            # Use text() for raw SQL and bind params if needed, but here simple query is fine
            query = text("SELECT title FROM learning_materials WHERE title LIKE 'Oversikt%' ORDER BY title")
            with conn.connect() as connection:
                result = connection.execute(query)
                print("Found 'Oversikt' articles:")
                for row in result:
                    print(f"- {row[0]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_titles()
