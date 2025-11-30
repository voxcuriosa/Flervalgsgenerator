from storage import get_db_connection
from sqlalchemy import text
import pandas as pd
import os

def generate_html():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return

    # Fetch all data
    query = "SELECT * FROM learning_materials ORDER BY subject, topic, title"
    df = pd.read_sql(query, conn)
    
    # Build Hierarchy: Subject -> Level 1 (Historiske perioder) -> Level 2 (Eldre historie) -> Level 3 (Specific Topic) -> Articles
    hierarchy = {}
    
    for _, row in df.iterrows():
        subject = row['subject']
        path_str = row['path']
        
        if not path_str:
            # Fallback for old data or missing paths
            path_parts = ["Diverse", row['topic']]
        else:
            path_parts = path_str.split(" > ")
            
        # Navigate/Build tree
        current_level = hierarchy.setdefault(subject, {})
        
        for part in path_parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
            
        if "_articles" not in current_level:
            current_level["_articles"] = []
        current_level["_articles"].append(row)

    # Recursive HTML Generation
    def generate_html_recursive(node, level, parent_slug=""):
        html = ""
        
        # 1. Render Articles in this node
        if "_articles" in node:
            articles = node["_articles"]
            # Check if we should hide the header (single article with same name as parent)
            # But here we don't have the parent name easily available unless passed.
            # Actually, the header is rendered by the caller (parent).
            # So we just render cards here.
            
            for row in articles:
                title = row['title']
                content = row['content'].replace("\n", "<br>")
                url = row['url']
                art_slug = f"{parent_slug}-{title}".replace(" ", "-").replace(":", "").replace(",", "").lower()
                
                html += f"""
                <details class="article-card" id="{art_slug}">
                    <summary class="article-summary">{title}</summary>
                    <div class="article-content">
                        {content}
                        <br>
                        <a href="{url}" target="_blank" class="original-link">Les original på NDLA &rarr;</a>
                    </div>
                </details>
                """
        
        # 2. Render Sub-topics
        for key, value in node.items():
            if key == "_articles": continue
            
            slug = f"{parent_slug}-{key}".replace(" ", "-").replace(":", "").replace(",", "").lower()
            
            # Header size based on level
            # Level 1 (Subject) is handled outside.
            # Level 1 here is "Historiske perioder" etc. -> h2 (or div with class)
            # Level 2 -> h3
            
            # We use the CSS classes we defined: level1-header, level2-header, topic-header
            if level == 1:
                header_class = "level1-header"
                container_class = ""
            elif level == 2:
                header_class = "level2-header"
                container_class = ""
            else:
                header_class = "topic-header"
                container_class = "topic-section"
            
            # Special check for "Å dele i perioder" style redundancy
            # If this node has only 1 child which is an article, and names match...
            # But wait, 'value' is the child node.
            # If 'value' has '_articles' and len is 1 and title matches 'key'...
            
            show_header = True
            if "_articles" in value and len(value["_articles"]) == 1:
                if value["_articles"][0]['title'] == key:
                    show_header = False
            
            # If it's a topic section (level 3+), wrap in box
            if level >= 3:
                html += f'<div id="{slug}" class="{container_class}">'
                if show_header:
                    html += f'<h2 class="{header_class}">{key}</h2>'
                html += generate_html_recursive(value, level + 1, slug)
                html += '</div>'
            else:
                # Higher levels are just structural dividers
                html += f'<div id="{slug}">'
                html += f'<div class="{header_class}">{key}</div>'
                html += generate_html_recursive(value, level + 1, slug)
                html += '</div>'
                
        return html

    # Generate Sidebar
    # We assume only one subject "Historie vg2"
    # Iterate the root node directly
    
    # Sort keys: "Diverse" last, others alphabetically
    root_keys = list(hierarchy.values())[0].keys() # Assuming 1 subject
    # Wait, hierarchy structure is {Subject: {L1: ...}}
    # So root_node is hierarchy["Historie vg2"]
    
    # Let's get the root node safely
    if hierarchy:
        subject = list(hierarchy.keys())[0]
        root_node = hierarchy[subject]
        
        sorted_keys = sorted([k for k in root_node.keys() if k != "_articles"])
        if "Diverse" in sorted_keys:
            sorted_keys.remove("Diverse")
            sorted_keys.append("Diverse")
            
        # We need to pass the sorted keys or iterate them here.
        # But generate_sidebar_recursive handles recursion.
        # We should modify generate_sidebar_recursive to handle sorting internally?
        # Or just call it on sorted items here?
        # The recursive function iterates node.items().
        
        # Let's modify the recursive function to handle sorting and collapsibility.
        
    def generate_sidebar_recursive(node, level, parent_slug=""):
        html = ""
        
        # Sort keys: "Diverse" last, others alphabetically
        keys = [k for k in node.keys() if k != "_articles"]
        keys.sort()
        if "Diverse" in keys:
            keys.remove("Diverse")
            keys.append("Diverse")
        
        for key in keys:
            value = node[key]
            slug = f"{parent_slug}-{key}".replace(" ", "-").replace(":", "").replace(",", "").lower()
            
            if level == 1:
                # Level 1: Main Topic (e.g. "Makt og religion") -> H2
                # Collapsible (Closed by default)
                html += f"""
                <details>
                    <summary><h2>{key}</h2></summary>
                    <div class="sidebar-section">
                        {generate_sidebar_recursive(value, level + 1, slug)}
                    </div>
                </details>
                """
            elif level == 2:
                # Level 2: Subtopic (e.g. "Fordeling og legitimering av makt") -> H3
                
                # Check if this is the ONLY Level 2 item (Redundancy check)
                if len(keys) == 1:
                    # Flatten: Skip header, just render content in UL
                    html += "<ul>"
                    
                    # 1. List Articles
                    if "_articles" in value:
                        articles = sorted(value["_articles"], key=lambda x: x['title'])
                        for row in articles:
                            art_slug = f"{slug}-{row['title']}".replace(" ", "-").replace(":", "").replace(",", "").lower()
                            html += f'<li><a href="#" onclick="var el = document.getElementById(\'{art_slug}\'); if(el) {{ el.open = true; el.scrollIntoView({{behavior: \'smooth\', block: \'center\'}}); }} return false;">{row["title"]}</a></li>'
                    
                    # 2. Recurse
                    html += generate_sidebar_recursive(value, level + 1, slug)
                    html += "</ul>"
                else:
                    # Normal: Collapsible Header
                    html += f"""
                    <details class="nav-level-2">
                        <summary><h3>{key}</h3></summary>
                        <ul>
                    """
                    
                    # 1. List Articles directly under this subtopic (Level 3)
                    if "_articles" in value:
                        # Sort articles by title
                        articles = sorted(value["_articles"], key=lambda x: x['title'])
                        for row in articles:
                            art_slug = f"{slug}-{row['title']}".replace(" ", "-").replace(":", "").replace(",", "").lower()
                            html += f'<li><a href="#" onclick="var el = document.getElementById(\'{art_slug}\'); if(el) {{ el.open = true; el.scrollIntoView({{behavior: \'smooth\', block: \'center\'}}); }} return false;">{row["title"]}</a></li>'
                    
                    # 2. Recurse for deeper levels
                    html += generate_sidebar_recursive(value, level + 1, slug)
                    html += """
                        </ul>
                    </details>
                    """
            else:
                # Level 3+: Just list as items
                # If it has children, maybe collapsible too?
                has_children = any(k != "_articles" for k in value.keys())
                
                if has_children:
                    html += f"""
                    <li>
                        <details>
                            <summary><a href="#" onclick="document.getElementById(\'{slug}\').scrollIntoView({{behavior: \'smooth\'}}); return false;" style="display:inline;">{key}</a></summary>
                            <ul>
                                {generate_sidebar_recursive(value, level + 1, slug)}
                            </ul>
                        </details>
                    </li>
                    """
                else:
                    html += f'<li><a href="#" onclick="document.getElementById(\'{slug}\').scrollIntoView({{behavior: \'smooth\'}}); return false;">{key}</a></li>'
                     
        return html

    # ... (rest of the code)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="no">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NDLA Historie Arkiv</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                display: flex;
                height: 100vh;
                background-color: #f4f4f9;
                color: #333;
            }
            /* Sidebar */
            .sidebar {
                width: 280px; /* Reduced from 450px */
                background-color: #2c3e50;
                color: white;
                padding: 15px;
                overflow-y: auto;
                flex-shrink: 0;
                font-size: 0.9em; /* Overall smaller font in sidebar */
            }
            
            /* Navigation Items Spacing */
            .nav-level-1 {
                margin-top: 15px;
                margin-bottom: 5px;
                border-bottom: 1px solid #34495e;
                padding-bottom: 5px;
                font-size: 1.1em; /* Reduced */
            }
            .nav-level-2 {
                margin-top: 8px;
                margin-bottom: 4px;
                margin-left: 8px;
            }
            
            /* Indentation for Level 2 items (inside Level 1) */
            .sidebar-section {
                margin-left: 10px;
            }
            
            /* Reset Header Margins in Sidebar */
            .sidebar h2 {
                font-size: 1.0em; /* Reduced */
                margin: 0;
                color: #ecf0f1;
                border: none;
            }
            .sidebar h3 {
                font-size: 0.9em; /* Reduced */
                margin: 0;
                color: #bdc3c7;
                font-weight: 600;
            }
            .sidebar h4 {
                font-size: 0.85em; /* Reduced */
                margin-left: 15px;
                margin-top: 4px;
                margin-bottom: 4px;
                color: #95a5a6;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .sidebar ul {
                list-style: none;
                padding: 0;
                margin-left: 15px;
            }
            .sidebar li {
                margin-bottom: 1px;
            }
            .sidebar a {
                color: #ecf0f1;
                text-decoration: none;
                display: block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.85em;
                transition: background 0.2s;
            }
            .sidebar a:hover {
                background-color: #34495e;
            }
            
            /* Main Content */
            .main-content {
                flex-grow: 1;
                padding: 40px;
                overflow-y: auto;
            }
            .subject-header { font-size: 2.2em; color: #2c3e50; margin-bottom: 10px; }
            .level1-header { font-size: 1.8em; color: #34495e; margin-bottom: 20px; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px; }
            .level2-header { font-size: 1.5em; color: #7f8c8d; margin-bottom: 15px; margin-top: 30px; }
            .topic-header { font-size: 1.3em; color: #2980b9; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
            
            .topic-section {
                margin-bottom: 40px;
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            
            /* Article Card */
            .article-card {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-bottom: 10px;
                background: #fff;
            }
            .article-summary {
                padding: 12px 15px;
                cursor: pointer;
                font-weight: 500;
                color: #34495e;
                background-color: #fcfcfc;
            }
            .article-summary:hover {
                background-color: #f0f2f5;
                color: #2980b9;
            }
            .article-content {
                padding: 20px;
                border-top: 1px solid #e0e0e0;
                line-height: 1.6;
                color: #444;
                font-size: 0.95em;
            }
            .original-link {
                display: inline-block;
                margin-top: 15px;
                color: #e74c3c;
                text-decoration: none;
                font-weight: bold;
                font-size: 0.9em;
            }
            .original-link:hover {
                text-decoration: underline;
            }
            
            /* Collapsible Sidebar */
            details > summary {
                list-style: none;
                cursor: pointer;
                display: flex; /* Flexbox for alignment */
                align-items: flex-start; /* Align top in case of wrapping */
            }
            details > summary::-webkit-details-marker {
                display: none;
            }
            details > summary:before {
                content: '▶';
                font-size: 0.8em;
                margin-right: 8px;
                margin-top: 4px; /* Align with text baseline approx */
                flex-shrink: 0;
                transition: transform 0.2s;
            }
            details[open] > summary:before {
                transform: rotate(90deg);
            }
        </style>
    </head>
    <body>

    <div class="sidebar">
        <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 20px; color: #3498db;">Innhold</div>
    """

    # Generate Sidebar Loop
    # Custom Sort Order
    subject_order = ["Historie vg2", "Historie vg3", "Historie (PB)", "Sosiologi og sosialantropologi", "Samfunnskunnskap"]
    
    def get_sort_key(subject_name):
        if subject_name in subject_order:
            return (subject_order.index(subject_name), subject_name)
        return (999, subject_name)
        
    sorted_subjects = sorted(hierarchy.keys(), key=get_sort_key)

    for subject in sorted_subjects:
        root_node = hierarchy[subject]
        html_content += f'<div class="nav-level-1" style="color: #e67e22; font-weight: bold; padding-left: 10px; margin-top: 20px;">{subject}</div>'
        html_content += generate_sidebar_recursive(root_node, 1, subject)
    
    html_content += """
    </div>

    <div class="main-content">
    """
    
    # Generate Content
    # Custom Sort Order
    subject_order = ["Historie vg2", "Historie vg3", "Historie (PB)", "Sosiologi og sosialantropologi", "Samfunnskunnskap"]
    
    def get_sort_key(subject_name):
        if subject_name in subject_order:
            return (subject_order.index(subject_name), subject_name)
        return (999, subject_name)
    
    sorted_subjects = sorted(hierarchy.keys(), key=get_sort_key)

    for subject in sorted_subjects:
        root_node = hierarchy[subject]
        html_content += f'<h1 class="subject-header">{subject}</h1>'
        html_content += generate_html_recursive(root_node, 1, subject)

    html_content += """
    </div>
    </body>
    </html>
    """
    
    output_file = "ndla_content_viewer.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Successfully generated {output_file}")
    print(f"Total articles: {len(df)}")

if __name__ == "__main__":
    generate_html()
