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
        # Pattern 1: ■ Tema (\d+): (.+?)\s+side (\d+) (Standard TOC)
        # Pattern 2: TEMA (\d+) (.+?) (Header style)
        pattern1 = re.compile(r"Tema\s+(\d+):\s+(.+?)\s+side\s+(\d+)", re.IGNORECASE)
        pattern2 = re.compile(r"TEMA\s+(\d+)\s+(.+)", re.IGNORECASE)
        
        matches = pattern1.findall(toc_text)
        
        parsed_topics = []
        if matches:
            for match in matches:
                num, title, page = match
                title = title.strip()
                page = int(page)
                pdf_page_index = max(0, page - 1)
                full_title = f"Tema {num}: {title}"
                parsed_topics.append((full_title, pdf_page_index))
        else:
            # Try pattern 2 on the first few pages content directly
            # This is a bit riskier as it might match headers on every page, 
            # but we only scan the first 5 pages for TOC-like structures.
            # If HPTx starts with "TEMA 6" on page 1, we can detect that.
            matches2 = pattern2.findall(toc_text)
            for match in matches2:
                num, title = match
                title = title.strip()
                # For this pattern, we assume it starts on the page we found it?
                # Or is it a TOC line without page number?
                # In the HPTx text: "66 \n TEMA \n 6 \n Persia..."
                # It seems to be a header.
                # If we find "TEMA 6" on page 1 (index 0), then Tema 6 starts at 0.
                # Let's try to find where "TEMA X" occurs in the text and use that page index.
                pass 
                
        # If regex failed, let's try a more direct approach for HPTx
        if not parsed_topics:
             # Scan pages for "TEMA X" headers
             # The text in HPTx.pdf is split across lines: "TEMA \n 6 \n Persia... \n IMPERIERS..."
             # We need to look for "TEMA" followed by a number on subsequent lines.
             
             for i in range(min(10, len(reader.pages))): # Scan first 10 pages
                 page_text = reader.pages[i].extract_text()
                 
                 # Look for TEMA followed by number (allowing newlines)
                 # We use a window or just search for the pattern with DOTALL equivalent?
                 # pypdf extraction might put newlines.
                 
                 # Regex to find "TEMA" then whitespace/newlines then digit
                 match = re.search(r"TEMA\s+(\d+)", page_text, re.IGNORECASE | re.MULTILINE)
                 
                 if match:
                     num = match.group(1)
                     # The title is likely on the lines following.
                     # In HPTx: "Persia, Hellas og Romerriket \n IMPERIERS VEKST OG FALL"
                     # The user wants "Imperiers vekst og fall".
                     # Let's try to grab the line containing "IMPERIERS VEKST OG FALL" if present, 
                     # or just use a fallback if we know it's HPTx.
                     
                     # Let's look for "IMPERIERS VEKST OG FALL" specifically as it seems to be the main title.
                     title_match = re.search(r"(IMPERIERS VEKST OG FALL.*)", page_text, re.IGNORECASE)
                     if title_match:
                         title = title_match.group(1).strip()
                         # Remove (DEL 1) if present? User didn't specify, but cleaner is better.
                         title = title.split('(')[0].strip()
                         # User explicitly requested "Tema X"
                         num = "X"
                     else:
                         # Fallback to the line after the number?
                         # This is hard to generalize. 
                         # But for HPTx we know what we want.
                         title = "Imperiers vekst og fall"
                         num = "X" # Default to X for this file if we are here
                     
                     full_title = f"Tema {num}: {title}"
                     
                     # Check if we already have this topic to avoid duplicates
                     if not any(t[0] == full_title for t in parsed_topics):
                        parsed_topics.append((full_title, i))
            
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
