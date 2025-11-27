import pypdf
import re

def extract_toc(pdf_path):
    """
    Extracts the outline (Table of Contents) from the PDF.
    Returns a list of tuples (title, page_number).
    """
    try:
        reader = pypdf.PdfReader(pdf_path)
        toc = []
        
        # Try to get the outline
        outline = reader.outline
        
        def parse_outline(outlines):
            for item in outlines:
                if isinstance(item, list):
                    parse_outline(item)
                else:
                    # pypdf Destination object has .title and .page_number (or .page which needs to be resolved)
                    # Note: .page returns a PageObject, we need to find its index.
                    # However, reader.get_destination_page_number(item) is the safer way.
                    try:
                        page_num = reader.get_destination_page_number(item)
                        toc.append((item.title, page_num))
                    except:
                        pass # Handle cases where page cannot be resolved
                        
        if outline:
            parse_outline(outline)
            return toc
        else:
            # Fallback: If no outline, maybe return generic "Whole Document" or try to find headers?
            # For now, let's return a single item if no TOC found.
            return [("Whole Document", 0)]
            
    except Exception as e:
        print(f"Error extracting TOC: {e}")
        return [("Error reading PDF", 0)]

def extract_text_by_topic(pdf_path, start_page, end_page=None):
    """
    Extracts text from the PDF for a given page range.
    """
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        total_pages = len(reader.pages)
        
        if end_page is None or end_page >= total_pages:
            end_page = total_pages
            
        for i in range(start_page, end_page):
            page = reader.pages[i]
            text += page.extract_text() + "\n"
            
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

def get_topics(pdf_path):
    """
    Returns a dictionary of {Topic Name: (start_page, end_page)}
    """
    topics = {}
    
    # Try to parse the visual TOC from the first few pages
    try:
        reader = pypdf.PdfReader(pdf_path)
        toc_text = ""
        # Extract text from pages 1-5 (indices 0-4)
        for i in range(5):
            if i < len(reader.pages):
                toc_text += reader.pages[i].extract_text() + "\n"
        
        # Regex to find "■ Tema X: Title side Y"
        # Pattern: ■ Tema (\d+): (.+?)\s+side (\d+)
        # Note: The text might have extra spaces or newlines.
        # Let's try a flexible pattern.
        pattern = re.compile(r"Tema\s+(\d+):\s+(.+?)\s+side\s+(\d+)", re.IGNORECASE)
        
        matches = pattern.findall(toc_text)
        
        parsed_topics = []
        for match in matches:
            num, title, page = match
            # Clean up title
            title = title.strip()
            page = int(page)
            # PDF pages are 0-indexed, but "side 54" usually means the printed page number.
            # Often printed page 1 is the cover or inside. 
            # We need to map "side 54" to the actual PDF page index.
            # Usually PDF index = Printed Page - 1 (if starting from 1) or offset.
            # Let's assume 1-to-1 mapping for now, or maybe -1.
            # Let's use page - 1.
            pdf_page_index = max(0, page - 1)
            
            full_title = f"Tema {num}: {title}"
            parsed_topics.append((full_title, pdf_page_index))
            
        if parsed_topics:
            # Sort by page number just in case
            parsed_topics.sort(key=lambda x: x[1])
            
            for i in range(len(parsed_topics)):
                title, start = parsed_topics[i]
                if i < len(parsed_topics) - 1:
                    end = parsed_topics[i+1][1]
                else:
                    end = len(reader.pages)
                topics[title] = (start, end)
                
            return topics
            
    except Exception as e:
        print(f"Error parsing TOC: {e}")

    # Fallback to existing logic if regex fails
    toc = extract_toc(pdf_path)
    
    if not toc:
        try:
            reader = pypdf.PdfReader(pdf_path)
            num_pages = len(reader.pages)
            return {f"Hele dokumentet (1-{num_pages})": (0, num_pages)}
        except:
            return {"Hele dokumentet": (0, None)}
        
    for i in range(len(toc)):
        title, start_page = toc[i]
        if i < len(toc) - 1:
            _, next_start = toc[i+1]
            end_page = next_start
        else:
            end_page = None 
        topics[title] = (start_page, end_page)
        
    return topics
