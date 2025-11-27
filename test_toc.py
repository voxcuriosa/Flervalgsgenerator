from pdf_processor import get_topics

def test():
    topics = get_topics("HPT.pdf")
    print(f"Found {len(topics)} topics.")
    for title, (start, end) in topics.items():
        print(f"{title}: {start} - {end}")

if __name__ == "__main__":
    test()
