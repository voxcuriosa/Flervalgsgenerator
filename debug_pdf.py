import pypdf

def debug_pdf(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        print(f"Number of pages: {len(reader.pages)}")
        
        if reader.outline:
            print("Outline found:")
            for item in reader.outline:
                print(item)
        else:
            print("No outline found in PDF.")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    debug_pdf("HPT.pdf")
