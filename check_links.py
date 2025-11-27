from storage import get_db_connection
import pandas as pd
import requests

def check_links():
    conn = get_db_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT id, title, url FROM learning_materials", conn)
            print(f"Checking {len(df)} links...")
            
            for index, row in df.iterrows():
                url = row['url']
                try:
                    response = requests.head(url, allow_redirects=True, timeout=5)
                    status = response.status_code
                    print(f"ID {row['id']}: {status} - {row['title']}")
                    print(f"  URL: {url}")
                    if status != 200:
                        print(f"  -> BROKEN or REDIRECT issue")
                except Exception as e:
                    print(f"ID {row['id']}: ERROR - {row['title']}")
                    print(f"  URL: {url}")
                    print(f"  Error: {e}")
                print("-" * 30)
                
        except Exception as e:
            print(f"Error querying database: {e}")
    else:
        print("Failed to connect to database.")

if __name__ == "__main__":
    check_links()
