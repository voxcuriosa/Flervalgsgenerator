import pypdf

def inspect_toc_pages(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        # Check pages 2 to 6 (index 1 to 5)
        for i in range(1, 6):
            print(f"\n--- Page {i+1} ---\n")
            print(reader.pages[i].extract_text())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_toc_pages("HPT.pdf")
