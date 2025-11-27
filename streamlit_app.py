import streamlit as st
import pandas as pd
import os
from pdf_processor import get_topics, extract_text_by_topic
from quiz_generator import generate_quiz
from storage import save_result, get_content_hierarchy
from pdf_generator import generate_quiz_pdf
from ndla_selector import render_ndla_selector
from generate_html_viewer import generate_html
import streamlit_oauth as oauth
import asyncio
import streamlit.components.v1 as components

# Page Config
st.set_page_config(page_title="HPT Quiz Generator", layout="wide")

# Constants
PDF_PATH = "HPT.pdf"
HTML_VIEWER_PATH = "ndla_content_viewer.html"
LOGO_URL = "logo.png"

def apply_custom_css():
    st.markdown("""
        <style>
        /* Main Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Background - Dark */
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        
        /* Sidebar - Slightly lighter dark */
        [data-testid="stSidebar"] {
            background-color: #262730;
            border-right: 1px solid #333;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-weight: 600;
            color: #ffffff !important;
        }
        
        /* Buttons */
        .stButton button {
            background-color: #4c4cff; /* Accent color */
            color: white !important;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #3b3bff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        
        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            border-radius: 8px;
            border: 1px solid #444;
            background-color: #1a1c24;
            color: white;
        }
        
        /* Cards/Containers */
        .css-1r6slb0 {
            background-color: #1a1c24;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        
        /* Links */
        a {
            color: #4c4cff !important;
        }
        
        /* Checkbox/Radio text */
        .stCheckbox label, .stRadio label {
            color: #fafafa;
        }
        </style>
    """, unsafe_allow_html=True)

def render_ndla_viewer():
    st.header("NDLA Fagstoff")
    
    # Ensure HTML exists
    if not os.path.exists(HTML_VIEWER_PATH):
        with st.spinner("Genererer innholdsvisning..."):
            generate_html()
            
    # Read HTML content
    try:
        with open(HTML_VIEWER_PATH, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        # Embed HTML
        # Height needs to be sufficient, scrolling=True handles overflow
        components.html(html_content, height=800, scrolling=True)
        
        st.info("Innholdet hentes fra lokal database basert på NDLA-skraping.")
    except Exception as e:
        st.error(f"Kunne ikke laste innholdsvisning: {e}")

def render_quiz_generator():
    # --- Admin View ---
    if st.session_state.get("user_email") == "borchgrevink@gmail.com":
        if st.sidebar.checkbox("Vis Admin-panel", key="admin_panel"):
            st.header("Admin: Resultater (fra Database)")
            
            st.markdown("""
            **Verktøy:**
            - [Åpne NDLA Database-visning](http://localhost:8000/ndla_content_viewer.html) (Krever at server kjører lokalt)
            """)
            
            # Import the new function
            from storage import get_all_results
            
            df = get_all_results()
            
            if not df.empty:
                # --- User Selection ---
                users = df['user_email'].unique()
                selected_user = st.selectbox("Velg bruker for detaljer", ["Alle"] + list(users))
                
                if selected_user != "Alle":
                    st.subheader(f"Resultater for: {selected_user}")
                    user_df = df[df['user_email'] == selected_user]
                    
                    # --- Summary Stats ---
                    total_quizzes = len(user_df)
                    total_questions = user_df['total'].sum()
                    total_score = user_df['score'].sum()
                    avg_score = user_df['percentage'].mean()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Antall Quizer", total_quizzes)
                    col2.metric("Totalt Spørsmål", total_questions)
                    col3.metric("Totalt Poeng", total_score)
                    col4.metric("Snitt Score", f"{avg_score:.1f}%")
                    
                    # --- Topic Breakdown ---
                    st.write("### Resultater per tema")
                    topic_stats = user_df.groupby('topic').agg({
                        'score': 'sum',
                        'total': 'sum',
                        'percentage': 'mean',
                        'timestamp': 'count' # Count quizzes per topic
                    }).rename(columns={'timestamp': 'antall_quizer'}).reset_index()
                    
                    topic_stats['snitt_prosent'] = topic_stats['percentage'].map('{:.1f}%'.format)
                    
                    st.dataframe(topic_stats[['topic', 'antall_quizer', 'score', 'total', 'snitt_prosent']], hide_index=True)
                    
                    st.write("### Historikk")
                    st.dataframe(user_df)
                else:
                    # Show all results
                    st.dataframe(df)
                
                # Download button (always available)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Last ned alle resultater (CSV)",
                    csv,
                    "quiz_results.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.info("Ingen resultater funnet ennå.")
            st.write("---")

    # --- App Logic ---
    
    # Check PDF
    if not os.path.exists(PDF_PATH):
        st.error(f"Fant ikke filen: {PDF_PATH}")
        return

    # Sidebar
    st.sidebar.header("Innstillinger")
    
    # Source Selection
    source_type = st.sidebar.radio("Velg kilde:", ["HPT Boka (PDF)", "NDLA (Nettressurs)"])
    
    selected_text = ""
    selected_topic_name = ""
    
    if source_type == "HPT Boka (PDF)":
        # Topics
        if "topics" not in st.session_state or st.sidebar.button("Oppdater temaer"):
            with st.spinner("Analyserer PDF..."):
                st.session_state.topics = get_topics(PDF_PATH)
                
        topic_names = list(st.session_state.topics.keys())
        st.sidebar.write(f"Fant {len(topic_names)} temaer.") # Debug info
        
        # Using a key ensures the selection persists even if other things update
        selected_topic = st.sidebar.selectbox("Velg tema", topic_names, key="topic_selector")
        selected_topic_name = selected_topic
        
    else: # NDLA
        st.sidebar.info("Velg emner og artikler fra NDLA-databasen nedenfor.")
        hierarchy = get_content_hierarchy()
        
        with st.sidebar.expander("Velg NDLA-innhold", expanded=True):
            selected_articles = render_ndla_selector(hierarchy)
            
        if selected_articles:
            st.sidebar.success(f"Valgt {len(selected_articles)} artikler.")
            # Combine text
            selected_text = "\n\n".join([art['content'] for art in selected_articles])
            # Topic name? Maybe "NDLA Utvalg" or list topics?
            if len(selected_articles) == 1:
                selected_topic_name = selected_articles[0]['title']
            else:
                selected_topic_name = f"NDLA Utvalg ({len(selected_articles)} artikler)"
        else:
            st.sidebar.warning("Ingen artikler valgt.")
    
    num_questions = st.sidebar.slider("Antall spørsmål", 1, 100, 5)
    num_options = st.sidebar.slider("Antall svaralternativer", 2, 6, 4)
    multiple_correct = st.sidebar.checkbox("Flere rette svar (maks 2)", value=False)
    
    if st.sidebar.button("Generer Quiz"):
        if source_type == "HPT Boka (PDF)":
            start_page, end_page = st.session_state.topics[selected_topic]
            with st.spinner(f"Henter tekst fra {selected_topic}..."):
                text = extract_text_by_topic(PDF_PATH, start_page, end_page)
        else:
            # NDLA
            if not selected_text:
                st.error("Du må velge minst én artikkel fra NDLA.")
                st.stop()
            text = selected_text
            
        with st.spinner("Genererer spørsmål med AI..."):
            quiz_data = generate_quiz(text, num_questions, num_options, multiple_correct)
            
            if "error" in quiz_data:
                st.error(f"Feil ved generering: {quiz_data['error']}")
            else:
                st.session_state.quiz_data = quiz_data
                st.session_state.current_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.selected_topic_name = selected_topic_name # Store for results
                st.rerun()

    # Display Quiz
    if "quiz_data" in st.session_state and not st.session_state.get("quiz_submitted", False):
        topic_display = st.session_state.get("selected_topic_name", "Quiz")
        st.header(f"Quiz: {topic_display}")
        
        form = st.form("quiz_form")
        questions = st.session_state.quiz_data.get("questions", [])
        
        user_answers = {}
        
        for i, q in enumerate(questions):
            form.subheader(f"{i+1}. {q['question']}")
            
            options = q['options']
            
            if multiple_correct:
                # Checkboxes
                selected = []
                for j, opt in enumerate(options):
                    if form.checkbox(opt, key=f"q{i}_opt{j}"):
                        selected.append(j)
                user_answers[i] = selected
            else:
                # Radio
                selected = form.radio("Velg svar:", options, key=f"q{i}", index=None)
                # Map back to index
                if selected:
                    user_answers[i] = [options.index(selected)]
                else:
                    user_answers[i] = []
                    
            form.write("---")
            
        if form.form_submit_button("Lever svar"):
            st.session_state.current_answers = user_answers
            st.session_state.quiz_submitted = True
            st.rerun()

    # Display Results
    if st.session_state.get("quiz_submitted", False):
        st.header("Resultater")
        
        questions = st.session_state.quiz_data.get("questions", [])
        answers = st.session_state.current_answers
        
        score = 0
        total_possible = 0
        
        for i, q in enumerate(questions):
            correct_indices = q['correct_indices']
            user_indices = answers.get(i, [])
            
            q_score = 0
            q_max = len(correct_indices)
            
            # Let's calculate points
            for idx in user_indices:
                if idx in correct_indices:
                    q_score += 1
                else:
                    pass
            
            # If single choice, max is 1.
            score += q_score
            total_possible += q_max
            
            # Display feedback
            st.subheader(f"Spørsmål {i+1}")
            st.write(q['question'])
            
            # Show options with colors
            for j, opt in enumerate(q['options']):
                prefix = ""
                color = "black"
                
                is_selected = j in user_indices
                is_correct = j in correct_indices
                
                if is_selected and is_correct:
                    prefix = "✅ (Ditt svar - Riktig)"
                    color = "green"
                elif is_selected and not is_correct:
                    prefix = "❌ (Ditt svar - Feil)"
                    color = "red"
                elif not is_selected and is_correct:
                    prefix = "⚠️ (Riktig svar)"
                    color = "orange"
                else:
                    prefix = "⚪"
                    color = "gray" # 'black' is not supported in Streamlit markdown colors
                
                st.markdown(f":{color}[{prefix} {opt}]")
            
            st.info(f"Begrunnelse: {q.get('justification', 'Ingen begrunnelse.')}")
            st.write("---")
            
        percentage = (score / total_possible) * 100 if total_possible > 0 else 0
        if not st.session_state.get("result_saved", False):
            category = save_result(
                st.session_state.user_email, 
                st.session_state.user_name, 
                score, 
                total_possible, 
                percentage, 
                st.session_state.get("selected_topic_name", "Ukjent")
            )
            st.session_state.result_saved = True
            st.session_state.last_category = category
        else:
            category = st.session_state.get("last_category", "Ukjent")
        
        st.metric("Din poengsum", f"{score} / {total_possible}", f"{percentage:.1f}%")
        st.success(f"Resultat: {category}")
        
        # PDF Download
        pdf_bytes = generate_quiz_pdf(
            st.session_state.get("selected_topic_name", "Quiz"), 
            st.session_state.user_name, 
            score, 
            total_possible, 
            percentage, 
            questions, 
            answers
        )
        
        st.download_button(
            label="Last ned resultat (PDF)",
            data=pdf_bytes,
            file_name=f"quiz_resultat.pdf",
            mime="application/pdf"
        )
        
        if st.button("Ta ny quiz"):
            del st.session_state.quiz_data
            del st.session_state.quiz_submitted
            if "result_saved" in st.session_state:
                del st.session_state.result_saved
            st.rerun()

def main():
    apply_custom_css()
    
    # Logo in Sidebar
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.title("Flervalgsgenerator")
    
    if st.sidebar.button("Nullstill app (Debug)"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- Authentication ---
    if "google" not in st.secrets:
        st.error("Google secrets not found in .streamlit/secrets.toml")
        st.stop()
        
    client_id = st.secrets["google"]["client_id"]
    client_secret = st.secrets["google"]["client_secret"]
    redirect_uri = st.secrets["google"]["redirect_uri"]
    
    # Initialize OAuth2 object
    oauth2 = oauth.OAuth2Component(
        client_id, client_secret, 
        "https://accounts.google.com/o/oauth2/v2/auth", 
        "https://oauth2.googleapis.com/token", 
        None, 
        None
    )
    
    # Check if we are already logged in
    if "token" not in st.session_state:
        # Check if we have a code from the redirect
        # st.query_params is the new way in recent Streamlit versions
        query_params = st.query_params
        code = query_params.get("code")
        
        if code:
            try:
                # Exchange code for token
                import requests
                
                token_url = "https://oauth2.googleapis.com/token"
                data = {
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
                response = requests.post(token_url, data=data)
                result = response.json()
                
                if "access_token" in result:
                    st.session_state.token = result
                    
                    # Get user info
                    id_token = result.get("id_token")
                    if id_token:
                        import base64
                        import json
                        # Decode without verify
                        parts = id_token.split('.')
                        if len(parts) > 1:
                            payload_b64 = parts[1]
                            payload_b64 += '=' * (-len(payload_b64) % 4)
                            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                            st.session_state.user_email = payload.get("email")
                            st.session_state.user_name = payload.get("name", "Unknown")
                    
                    # Clear query params to clean URL
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"Feil ved innlogging: {result.get('error_description', result)}")
            except Exception as e:
                st.error(f"Feil under token-utveksling: {e}")
        else:
            # Show Login Button
            import urllib.parse
            
            # Ensure no whitespace in secrets
            client_id = client_id.strip()
            redirect_uri = redirect_uri.strip()
            
            scope = "openid email profile"
            
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": scope,
                "access_type": "offline",
                "prompt": "consent"
            }
            
            # Use quote_via=urllib.parse.quote to get %20 instead of + for spaces
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
            
            st.markdown(f'''
                <a href="{auth_url}" target="_blank">
                    <button style="
                        background-color: #4285F4; 
                        color: white; 
                        padding: 10px 20px; 
                        border: none; 
                        border-radius: 5px; 
                        cursor: pointer; 
                        font-size: 16px;
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    ">
                        <img src="https://www.google.com/favicon.ico" width="20" style="background: white; border-radius: 50%; padding: 2px;">
                        Logg inn med Google
                    </button>
                </a>
            ''', unsafe_allow_html=True)
            return
    else:
        st.write(f"Velkommen, {st.session_state.user_name}!")
        
        # --- Main Navigation ---
        # Using a sidebar radio to switch modes
        st.sidebar.title("Navigasjon")
        app_mode = st.sidebar.radio("Velg modul:", ["Quiz Generator", "NDLA Fagstoff"])
        
        if st.sidebar.button("Logg ut"):
            del st.session_state.token
            st.rerun()
            
        st.divider()
        
        if app_mode == "Quiz Generator":
            render_quiz_generator()
        elif app_mode == "NDLA Fagstoff":
            render_ndla_viewer()

if __name__ == "__main__":
    main()
