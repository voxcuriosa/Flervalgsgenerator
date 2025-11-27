import requests

urls = [
    # User reported broken
    "https://ndla.no/r/historie-vg2/vikingtiden/0944062828",
    "https://ndla.no/r/historie-vg2/a-reise-i-viking/512534575b",
    # Currently in DB (from check_links output)
    "https://ndla.no/r/historie-vg2/vikingtiden/703358f692",
    "https://ndla.no/r/historie-vg2/a-reise-i-viking/d13c84336a"
]

def verify():
    for url in urls:
        print(f"Checking: {url}")
        try:
            response = requests.get(url, allow_redirects=True)
            print(f"Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            print(f"Content Length: {len(response.text)}")
            if "Fant ikke siden" in response.text or "404" in response.text:
                print("-> Soft 404 detected in content")
            else:
                print("-> Content seems OK")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 30)

if __name__ == "__main__":
    verify()
