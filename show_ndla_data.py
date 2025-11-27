from storage import get_db_connection
import pandas as pd

def show_data():
    conn = get_db_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT id, title, content FROM learning_materials ORDER BY id", conn)
            if not df.empty:
                print("\n=== NDLA Learning Materials Content Verification ===")
                for index, row in df.iterrows():
                    print(f"\n[ID: {row['id']}] {row['title']}")
                    print("=" * 60)
                    content_preview = row['content'][:600].replace("\n", " ")
                    print(f"{content_preview}...")
                    print("-" * 60)
            else:
                print("No data found in learning_materials table.")
        except Exception as e:
            print(f"Error querying database: {e}")
    else:
        print("Failed to connect to database.")

if __name__ == "__main__":
    show_data()
