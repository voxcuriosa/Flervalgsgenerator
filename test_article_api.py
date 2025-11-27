import requests
import json

def fetch_article():
    # urn:article:27138 -> 27138
    article_id = "27138"
    # Try different ID formats
    ids_to_try = [article_id, f"urn:article:{article_id}"]
    
    base_url = "https://api.ndla.no/content/v1/articles"
    
    for aid in ids_to_try:
        url = f"{base_url}/{aid}"
        print(f"\nTesting article endpoint: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print("Success!")
                print("Keys:", data.keys())
                print(f"Title: {data.get('title')}")
                # Check for content
                content = data.get('content') or data.get('body')
                if content:
                    print(f"Content preview: {str(content)[:100]}...")
                else:
                    print("No direct content field found.")
            else:
                print(f"Failed with status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fetch_article()
