import pypdf

def extract_first_pages(pdf_path, num_pages=15):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for i in range(min(num_pages, len(reader.pages))):
            text += f"\n--- Page {i+1} ---\n"
            text += reader.pages[i].extract_text()
        print(text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_first_pages("HPT.pdf")
