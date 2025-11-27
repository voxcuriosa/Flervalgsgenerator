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
        specific_topic = row['topic']
        
        # Determine hierarchy based on topic name
        level1 = "Historiske perioder"
        
        if specific_topic == "Å dele i perioder":
            level2 = "Å dele i perioder" # It's a direct child of Historiske perioder
            # Or maybe we want it to be its own level 2? 
            # The user said: "Eldre historie er da under emnet 'Historiske perioder'. ... Nå kan du skrape det andre underemnet under Historiske perioder: Å dele i perioder"
            # So structure is:
            # Historie vg2 -> Historiske perioder -> Eldre historie -> [Topics]
            # Historie vg2 -> Historiske perioder -> Å dele i perioder -> [Articles]
            
            # Since "Å dele i perioder" is the topic name in DB, we can treat it as Level 2
            # But the articles inside it don't have a further subtopic in the DB currently (topic column is "Å dele i perioder")
            # So we can put them directly under Level 2
            
            # Let's adjust the loop to handle this
            pass
        else:
            level2 = "Eldre historie"

        if subject not in hierarchy:
            hierarchy[subject] = {}
        if level1 not in hierarchy[subject]:
            hierarchy[subject][level1] = {}
            
        if specific_topic == "Å dele i perioder":
            # Special case: The topic itself is the container
            if specific_topic not in hierarchy[subject][level1]:
                hierarchy[subject][level1][specific_topic] = {}
            
            # Use the topic name itself as the key, instead of "Artikler"
            # This allows us to detect redundancy later
            if specific_topic not in hierarchy[subject][level1][specific_topic]:
                hierarchy[subject][level1][specific_topic][specific_topic] = []
            hierarchy[subject][level1][specific_topic][specific_topic].append(row)
        else:
            # Standard Eldre Historie flow
            if level2 not in hierarchy[subject][level1]:
                hierarchy[subject][level1][level2] = {}
            if specific_topic not in hierarchy[subject][level1][level2]:
                hierarchy[subject][level1][level2][specific_topic] = []
            hierarchy[subject][level1][level2][specific_topic].append(row)

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
                width: 300px;
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                overflow-y: auto;
                flex-shrink: 0;
            }
            .sidebar h2 {
                font-size: 1.1em;
                margin-top: 20px;
                margin-bottom: 5px;
                color: #ecf0f1;
                border-bottom: 1px solid #34495e;
                padding-bottom: 5px;
            }
            .sidebar h3 {
                font-size: 1.0em;
                margin-left: 10px;
                margin-top: 10px;
                margin-bottom: 5px;
                color: #bdc3c7;
                font-weight: 600;
            }
            .sidebar h4 {
                font-size: 0.9em;
                margin-left: 20px;
                margin-top: 5px;
                margin-bottom: 5px;
                color: #95a5a6;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .sidebar ul {
                list-style: none;
                padding: 0;
                margin-left: 20px;
            }
            .sidebar li {
                margin-bottom: 2px;
            }
            .sidebar a {
                color: #ecf0f1;
                text-decoration: none;
                display: block;
                padding: 5px 10px;
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
            
            .topic-section {
                margin-bottom: 40px;
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .topic-header {
                color: #2980b9;
                margin-top: 0;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-bottom: 20px;
                font-size: 1.3em;
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
        </style>
    </head>
    <body>

    <div class="sidebar">
        <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 20px; color: #3498db;">Innhold</div>
    """
    
    # Generate Sidebar
    for subject, level1_items in hierarchy.items():
        html_content += f"<h2>{subject}</h2>"
        for level1, level2_items in level1_items.items():
            html_content += f"<h3>{level1}</h3>"
            for level2, topics in level2_items.items():
                html_content += f"<h4>{level2}</h4><ul>"
                for topic in topics.keys():
                    slug = f"{subject}-{level1}-{level2}-{topic}".replace(" ", "-").replace(":", "").lower()
                    # Only show sub-topic in sidebar if it's different from level2
                    display_text = topic
                    if topic == level2:
                        display_text = "Artikler" # Or just hide it? Let's keep it as "Artikler" or "Oversikt" for navigation
                    
                    html_content += f'<li><a href="#{slug}">{display_text}</a></li>'
                html_content += "</ul>"
    
    html_content += """
    </div>

    <div class="main-content">
    """
    
    # Generate Content
    for subject, level1_items in hierarchy.items():
        html_content += f'<h1 class="subject-header">{subject}</h1>'
        for level1, level2_items in level1_items.items():
            html_content += f'<div class="level1-header">{level1}</div>'
            for level2, topics in level2_items.items():
                html_content += f'<div class="level2-header">{level2}</div>'
                
                for topic, articles in topics.items():
                    slug = f"{subject}-{level1}-{level2}-{topic}".replace(" ", "-").replace(":", "").lower()
                    
                    # HIDE redundant header if topic name equals level 2 name
                    header_html = f'<h2 class="topic-header">{topic}</h2>'
                    if topic == level2:
                        header_html = "" 
                        
                    html_content += f"""
                    <div id="{slug}" class="topic-section">
                        {header_html}
                    """
                    
                    for row in articles:
                        title = row['title']
                        content = row['content'].replace("\n", "<br>")
                        url = row['url']
                        
                        html_content += f"""
                        <details class="article-card">
                            <summary class="article-summary">{title}</summary>
                            <div class="article-content">
                                {content}
                                <br>
                                <a href="{url}" target="_blank" class="original-link">Les original på NDLA &rarr;</a>
                            </div>
                        </details>
                        """
                    html_content += "</div>"

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
