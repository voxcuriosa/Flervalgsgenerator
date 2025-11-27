import streamlit as st

def render_ndla_selector(hierarchy):
    """
    Renders the NDLA content hierarchy using Streamlit widgets.
    Returns a list of selected article dictionaries.
    """
    selected_articles = []
    
    # We assume one subject "Historie vg2" for now, but iterate to be safe
    for subject, root_node in hierarchy.items():
        st.subheader(subject)
        _recursive_render(root_node, selected_articles, level=1, parent_key=subject)
        
    return selected_articles

def _recursive_render(node, selected_articles, level, parent_key):
    # Sort keys: "Diverse" last, others alphabetically
    keys = [k for k in node.keys() if k != "_articles"]
    keys.sort()
    if "Diverse" in keys:
        keys.remove("Diverse")
        keys.append("Diverse")
        
    # 1. Render Articles in this node
    if "_articles" in node:
        articles = sorted(node["_articles"], key=lambda x: x['title'])
        for article in articles:
            # Unique key for checkbox
            key = f"{parent_key}_{article['title']}"
            if st.checkbox(article['title'], key=key):
                selected_articles.append(article)
                
    # 2. Render Sub-topics
    for key in keys:
        value = node[key]
        new_key = f"{parent_key}_{key}"
        
        # Flatten single-child Level 2 topics logic (mirroring HTML viewer)
        # If level 2 and only 1 child (which is content or subtopic), maybe flatten?
        # But for selection, expanders are fine. 
        # However, user said "bla seg nedover".
        
        # Use expander for topics
        with st.expander(key, expanded=False):
            _recursive_render(value, selected_articles, level + 1, new_key)
