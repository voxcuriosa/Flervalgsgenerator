from storage import get_db_connection
from sqlalchemy import text
import pandas as pd
import os

def debug_content():
    print(f"DB Path: {os.path.abspath('learning_materials.db')}")
    if os.path.exists('learning_materials.db'):
        print(f"DB Size: {os.path.getsize('learning_materials.db')} bytes")
    
    engine = get_db_connection()
    if not engine:
        print("No engine")
        return

    # Check for "Oversikt: Antikken" (VG2)
    query = text("SELECT * FROM learning_materials WHERE title = :title")
    with engine.connect() as conn:
        result = conn.execute(query, {"title": "Oversikt: Antikken"}).fetchall()
        print(f"\nSearching for 'Oversikt: Antikken': Found {len(result)}")
        for row in result:
            print(f"  - Subject: {row.subject}, Topic: {row.topic}, ID: {row.id}")

    # Check for "Imperialismens tidsalder" (VG3)
    with engine.connect() as conn:
        result = conn.execute(query, {"title": "Imperialismens tidsalder"}).fetchall()
        print(f"\nSearching for 'Imperialismens tidsalder': Found {len(result)}")
        for row in result:
            print(f"  - Subject: {row.subject}, Topic: {row.topic}, ID: {row.id}")

if __name__ == "__main__":
    debug_content()
