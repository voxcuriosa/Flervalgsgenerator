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

# Translations
TRANSLATIONS = {
    "no": {
        "title": "Flervalgsgenerator",
        "login_google": "Logg inn med Google",
        "welcome": "Velkommen",
        "logout": "Logg ut",
        "navigation": "Navigasjon",
        "module_quiz": "Quiz Generator",
        "module_ndla": "NDLA Fagstoff",
        "settings": "Innstillinger",
        "source": "Velg kilde:",
        "source_pdf": "Historie på Tvers (Lærebok)",
        "source_ndla": "NDLA (Nettressurs)",
        "update_topics": "Oppdater temaer",
        "topics_found": "Fant {} temaer.",
        "select_topic": "Velg tema",
        "ndla_info": "Velg emner og artikler fra NDLA-databasen nedenfor.",
        "ndla_expand": "Velg NDLA-innhold",
        "selected_articles": "Valgt {} artikler.",
        "no_articles": "Ingen artikler valgt.",
        "num_questions": "Antall spørsmål",
        "num_options": "Antall svaralternativer",
        "multiple_correct": "Flere rette svar (maks 2)",
        "generate_btn": "Generer Quiz",
        "analyzing_pdf": "Analyserer PDF...",
        "fetching_text": "Henter tekst fra {}...",
        "error_ndla_select": "Du må velge minst én artikkel fra NDLA.",
        "generating": "Generer spørsmål med AI...",
        "error_gen": "Feil ved generering: {}",
        "quiz_header": "Quiz: {}",
        "submit_btn": "Lever svar",
        "results_header": "Resultater",
        "question": "Spørsmål",
        "your_answer_correct": "✅ (Ditt svar - Riktig)",
        "your_answer_wrong": "❌ (Ditt svar - Feil)",
        "correct_answer": "⚠️ (Riktig svar)",
        "justification": "Begrunnelse",
        "score": "Din poengsum",
        "result_cat": "Resultat: {}",
        "download_pdf": "Last ned resultat (PDF)",
        "new_quiz": "Ta ny quiz",
        "admin_panel": "Vis Admin-panel",
        "admin_header": "Admin: Resultater (fra Database)",
        "admin_tools": "**Verktøy:**\n- [Åpne NDLA Database-visning](http://localhost:8000/ndla_content_viewer.html) (Krever at server kjører lokalt)",
        "select_user": "Velg bruker for detaljer",
        "results_for": "Resultater for: {}",
        "total_quizzes": "Antall Quizer",
        "total_questions": "Totalt Spørsmål",
        "total_score": "Totalt Poeng",
        "avg_score": "Snitt Score",
        "results_per_topic": "Resultater per tema",
        "history": "Historikk",
        "download_csv": "Last ned alle resultater (CSV)",
        "no_results": "Ingen resultater funnet ennå.",
        "ndla_viewer_header": "NDLA Fagstoff",
        "ndla_viewer_info": "Innholdet hentes fra lokal database basert på NDLA-skraping.",
        "ndla_viewer_error": "Kunne ikke laste innholdsvisning: {}",
        "reset_app": "Nullstill app (Debug)"
    },
    "en": {
        "title": "Multiple Choice Generator",
        "login_google": "Login with Google",
        "welcome": "Welcome",
        "logout": "Log out",
        "navigation": "Navigation",
        "module_quiz": "Quiz Generator",
        "module_ndla": "NDLA Content",
        "settings": "Settings",
        "source": "Select Source:",
        "source_pdf": "Historie på Tvers (Textbook)",
        "source_ndla": "NDLA (Online Resource)",
        "update_topics": "Update Topics",
        "topics_found": "Found {} topics.",
        "select_topic": "Select Topic",
        "ndla_info": "Select topics and articles from the NDLA database below.",
        "ndla_expand": "Select NDLA Content",
        "selected_articles": "Selected {} articles.",
        "no_articles": "No articles selected.",
        "num_questions": "Number of Questions",
        "num_options": "Number of Options",
        "multiple_correct": "Multiple Correct Answers (max 2)",
        "generate_btn": "Generate Quiz",
        "analyzing_pdf": "Analyzing PDF...",
        "fetching_text": "Fetching text from {}...",
        "error_ndla_select": "You must select at least one article from NDLA.",
        "generating": "Generating questions with AI...",
        "error_gen": "Generation error: {}",
        "quiz_header": "Quiz: {}",
        "submit_btn": "Submit Answers",
        "results_header": "Results",
        "question": "Question",
        "your_answer_correct": "✅ (Your Answer - Correct)",
        "your_answer_wrong": "❌ (Your Answer - Wrong)",
        "correct_answer": "⚠️ (Correct Answer)",
        "justification": "Justification",
        "score": "Your Score",
        "result_cat": "Result: {}",
        "download_pdf": "Download Result (PDF)",
        "new_quiz": "Take New Quiz",
        "admin_panel": "Show Admin Panel",
        "admin_header": "Admin: Results (from Database)",
        "admin_tools": "**Tools:**\n- [Open NDLA Database View](http://localhost:8000/ndla_content_viewer.html) (Requires local server)",
        "select_user": "Select User for Details",
        "results_for": "Results for: {}",
        "total_quizzes": "Total Quizzes",
        "total_questions": "Total Questions",
        "total_score": "Total Score",
        "avg_score": "Avg Score",
        "results_per_topic": "Results per Topic",
        "history": "History",
        "download_csv": "Download All Results (CSV)",
        "no_results": "No results found yet.",
        "ndla_viewer_header": "NDLA Content",
        "ndla_viewer_info": "Content fetched from local database based on NDLA scraping.",
        "ndla_viewer_error": "Could not load content viewer: {}",
        "reset_app": "Reset App (Debug)"
    }
}

def get_text(key, *args):
    lang = st.session_state.get("language", "no")
    text = TRANSLATIONS[lang].get(key, key)
    if args:
        return text.format(*args)
    return text

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
            min-width: 400px; /* Widen sidebar */
            max-width: 600px;
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
    st.header(get_text("ndla_viewer_header"))
    
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
        
        st.info(get_text("ndla_viewer_info"))
    except Exception as e:
        st.error(get_text("ndla_viewer_error", e))

def render_quiz_generator():
    # --- Admin View ---
    if st.session_state.get("user_email") == "borchgrevink@gmail.com":
        if st.sidebar.checkbox(get_text("admin_panel"), key="admin_panel"):
            st.header(get_text("admin_header"))
            
            st.markdown(get_text("admin_tools"))
            
            # Import the new function
            from storage import get_all_results
            
            df = get_all_results()
            
            if not df.empty:
                # --- User Selection ---
                users = df['user_email'].unique()
                selected_user = st.selectbox(get_text("select_user"), ["Alle"] + list(users))
                
                if selected_user != "Alle":
                    st.subheader(get_text("results_for", selected_user))
                    user_df = df[df['user_email'] == selected_user]
                    
                    # --- Summary Stats ---
                    total_quizzes = len(user_df)
                    total_questions = user_df['total'].sum()
                    total_score = user_df['score'].sum()
                    avg_score = user_df['percentage'].mean()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric(get_text("total_quizzes"), total_quizzes)
                    col2.metric(get_text("total_questions"), total_questions)
                    col3.metric(get_text("total_score"), total_score)
                    col4.metric(get_text("avg_score"), f"{avg_score:.1f}%")
                    
                    # --- Topic Breakdown ---
                    st.write(f"### {get_text('results_per_topic')}")
                    topic_stats = user_df.groupby('topic').agg({
                        'score': 'sum',
                        'total': 'sum',
                        'percentage': 'mean',
                        'timestamp': 'count' # Count quizzes per topic
                    }).rename(columns={'timestamp': 'antall_quizer'}).reset_index()
                    
                    topic_stats['snitt_prosent'] = topic_stats['percentage'].map('{:.1f}%'.format)
                    
                    st.dataframe(topic_stats[['topic', 'antall_quizer', 'score', 'total', 'snitt_prosent']], hide_index=True)
                    
                    st.write(f"### {get_text('history')}")
                    st.dataframe(user_df)
                else:
                    # Show all results
                    st.dataframe(df)
                
                # Download button (always available)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    get_text("download_csv"),
                    csv,
                    "quiz_results.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.info(get_text("no_results"))
            st.write("---")

    # --- App Logic ---
    
    # Check PDF
    if not os.path.exists(PDF_PATH):
        st.error(f"Fant ikke filen: {PDF_PATH}")
        return

    # Sidebar
    st.sidebar.header(get_text("settings"))
    
    # Source Selection
    source_options = [get_text("source_pdf"), get_text("source_ndla")]
    source_type = st.sidebar.radio(get_text("source"), source_options)
    
    selected_text = ""
    selected_topic_name = ""
    
    if source_type == get_text("source_pdf"):
        # Topics
        if "topics" not in st.session_state or st.sidebar.button(get_text("update_topics")):
            with st.spinner(get_text("analyzing_pdf")):
                st.session_state.topics = get_topics(PDF_PATH)
                
        topic_names = list(st.session_state.topics.keys())
        st.sidebar.write(get_text("topics_found", len(topic_names))) # Debug info
        
        # Using a key ensures the selection persists even if other things update
        selected_topic = st.sidebar.selectbox(get_text("select_topic"), topic_names, key="topic_selector")
        selected_topic_name = selected_topic
        
    else: # NDLA
        st.sidebar.info(get_text("ndla_info"))
        hierarchy = get_content_hierarchy()
        
        with st.sidebar.expander(get_text("ndla_expand"), expanded=True):
            selected_articles = render_ndla_selector(hierarchy)
            
        if selected_articles:
            st.sidebar.success(get_text("selected_articles", len(selected_articles)))
            # Combine text
            selected_text = "\n\n".join([art['content'] for art in selected_articles])
            # Topic name? Maybe "NDLA Utvalg" or list topics?
            if len(selected_articles) == 1:
                selected_topic_name = selected_articles[0]['title']
            else:
                selected_topic_name = f"NDLA Utvalg ({len(selected_articles)} artikler)"
        else:
            st.sidebar.warning(get_text("no_articles"))
    
    num_questions = st.sidebar.slider(get_text("num_questions"), 1, 100, 5)
    num_options = st.sidebar.slider(get_text("num_options"), 2, 6, 4)
    multiple_correct = st.sidebar.checkbox(get_text("multiple_correct"), value=False)
    
    if st.sidebar.button(get_text("generate_btn")):
        if source_type == get_text("source_pdf"):
            start_page, end_page = st.session_state.topics[selected_topic]
            with st.spinner(get_text("fetching_text", selected_topic)):
                text = extract_text_by_topic(PDF_PATH, start_page, end_page)
        else:
            # NDLA
            if not selected_text:
                st.error(get_text("error_ndla_select"))
                st.stop()
            text = selected_text
            
        with st.spinner(get_text("generating")):
            # Pass language to generate_quiz
            lang = st.session_state.get("language", "no")
            quiz_data = generate_quiz(text, num_questions, num_options, multiple_correct, language=lang)
            
            if "error" in quiz_data:
                st.error(get_text("error_gen", quiz_data['error']))
            else:
                st.session_state.quiz_data = quiz_data
                st.session_state.current_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.selected_topic_name = selected_topic_name # Store for results
                st.rerun()

    # Display Quiz
    if "quiz_data" in st.session_state and not st.session_state.get("quiz_submitted", False):
        topic_display = st.session_state.get("selected_topic_name", "Quiz")
        st.header(get_text("quiz_header", topic_display))
        
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
            
        if form.form_submit_button(get_text("submit_btn")):
            st.session_state.current_answers = user_answers
            st.session_state.quiz_submitted = True
            st.rerun()

    # Display Results
    if st.session_state.get("quiz_submitted", False):
        st.header(get_text("results_header"))
        
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
            st.subheader(f"{get_text('question')} {i+1}")
            st.write(q['question'])
            
            # Show options with colors
            for j, opt in enumerate(q['options']):
                prefix = ""
                color = "black"
                
                is_selected = j in user_indices
                is_correct = j in correct_indices
                
                if is_selected and is_correct:
                    prefix = get_text("your_answer_correct")
                    color = "green"
                elif is_selected and not is_correct:
                    prefix = get_text("your_answer_wrong")
                    color = "red"
                elif not is_selected and is_correct:
                    prefix = get_text("correct_answer")
                    color = "orange"
                else:
                    prefix = "⚪"
                    color = "gray" # 'black' is not supported in Streamlit markdown colors
                
                st.markdown(f":{color}[{prefix} {opt}]")
            
            st.info(f"{get_text('justification')}: {q.get('justification', 'Ingen begrunnelse.')}")
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
        
        st.metric(get_text("score"), f"{score} / {total_possible}", f"{percentage:.1f}%")
        st.success(get_text("result_cat", category))
        
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
            label=get_text("download_pdf"),
            data=pdf_bytes,
            file_name=f"quiz_resultat.pdf",
            mime="application/pdf"
        )
        
        if st.button(get_text("new_quiz")):
            del st.session_state.quiz_data
            del st.session_state.quiz_submitted
            if "result_saved" in st.session_state:
                del st.session_state.result_saved
            st.rerun()

def main():
    apply_custom_css()
    
    # Initialize Language
    if "language" not in st.session_state:
        st.session_state.language = "no"
    
    # Logo in Sidebar
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.title(get_text("title"))
    
    # Language Selector
    lang_options = {"no": "🇳🇴 Norsk", "en": "🇬🇧 English"}
    selected_lang = st.sidebar.radio(
        "Language / Språk", 
        options=list(lang_options.keys()), 
        format_func=lambda x: lang_options[x],
        index=0 if st.session_state.language == "no" else 1,
        key="lang_selector"
    )
    
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
    
    if st.sidebar.button(get_text("reset_app")):
        for key in list(st.session_state.keys()):
            if key != "language": # Keep language
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
                        {get_text("login_google")}
                    </button>
                </a>
            ''', unsafe_allow_html=True)
            return
    else:
        st.write(f"{get_text('welcome')}, {st.session_state.user_name}!")
        
        # --- Main Navigation ---
        # Using a sidebar radio to switch modes
        st.sidebar.title(get_text("navigation"))
        app_mode = st.sidebar.radio(get_text("navigation"), [get_text("module_quiz"), get_text("module_ndla")], label_visibility="collapsed")
        
        if st.sidebar.button(get_text("logout")):
            del st.session_state.token
            st.rerun()
            
        st.divider()
        
        if app_mode == get_text("module_quiz"):
            render_quiz_generator()
        elif app_mode == get_text("module_ndla"):
            render_ndla_viewer()

if __name__ == "__main__":
    main()
