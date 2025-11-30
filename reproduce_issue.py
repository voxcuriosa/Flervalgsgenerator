import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Sidebar Toggle Button (Mobile) */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #4c4cff; /* High contrast blue */
        border: 2px solid white;
        border-radius: 8px;
        padding: 10px 15px; /* Larger padding */
        color: white;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
        z-index: 999999; /* Ensure it's on top */
        width: auto !important;
        height: auto !important;
    }
    
    /* Add "MENY" text */
    [data-testid="stSidebarCollapsedControl"]::after {
        content: "MENY";
        font-weight: 900;
        font-size: 18px; /* Larger font */
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: white;
        display: inline-block; /* Ensure it takes space */
    }
    
    [data-testid="stSidebarCollapsedControl"] svg {
        height: 28px !important; /* Larger icon */
        width: 28px !important;
        fill: white !important;
    }
    
    /* Make the header toolbar background visible on mobile to contrast the button */
    header[data-testid="stHeader"] {
        background-color: #0e1117;
        z-index: 99999;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Reproduction App")
st.write("Check the sidebar toggle button.")
