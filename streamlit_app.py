import streamlit as st
import pandas as pd
import os
from pdf_processor import get_topics, extract_text_by_topic
from quiz_generator import generate_quiz
from storage import save_result
import streamlit_oauth as oauth
import asyncio

# Page Config
st.set_page_config(page_title="HPT Quiz Generator", layout="wide")

# Constants
PDF_PATH = "HPT.pdf"

def main():
    st.title("HPT Flervalgsgenerator")
    
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
                # The library expects a specific format or we can do it manually if needed
                # But oauth2.client.get_access_token is async. 
                # We can use the component's helper or just requests.
                # Let's use requests for simplicity and control.
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
            # Generate Auth URL
            # Generate Auth URL manually to ensure exact format
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
        if st.button("Logg ut"):
            del st.session_state.token
            st.rerun()

    # --- Admin View ---
    if st.session_state.get("user_email") == "borchgrevink@gmail.com":
        if st.sidebar.checkbox("Vis Admin-panel", key="admin_panel"):
            st.header("Admin: Resultater (fra Database)")
            
            # Import the new function
            from storage import get_all_results
            
            df = get_all_results()
            
            if not df.empty:
                st.dataframe(df)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Last ned resultater",
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
    
    # Topics
    if "topics" not in st.session_state or st.sidebar.button("Oppdater temaer"):
        with st.spinner("Analyserer PDF..."):
            st.session_state.topics = get_topics(PDF_PATH)
            
    topic_names = list(st.session_state.topics.keys())
    st.sidebar.write(f"Fant {len(topic_names)} temaer.") # Debug info
    
    # Using a key ensures the selection persists even if other things update
    selected_topic = st.sidebar.selectbox("Velg tema", topic_names, key="topic_selector")
    
    num_questions = st.sidebar.slider("Antall spørsmål", 1, 20, 5)
    num_options = st.sidebar.slider("Antall svaralternativer", 2, 6, 4)
    multiple_correct = st.sidebar.checkbox("Flere rette svar (maks 2)", value=False)
    
    if st.sidebar.button("Generer Quiz"):
        start_page, end_page = st.session_state.topics[selected_topic]
        with st.spinner(f"Henter tekst fra {selected_topic}..."):
            text = extract_text_by_topic(PDF_PATH, start_page, end_page)
            
        with st.spinner("Genererer spørsmål med AI..."):
            quiz_data = generate_quiz(text, num_questions, num_options, multiple_correct)
            
            if "error" in quiz_data:
                st.error(f"Feil ved generering: {quiz_data['error']}")
            else:
                st.session_state.quiz_data = quiz_data
                st.session_state.current_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

    # Display Quiz
    if "quiz_data" in st.session_state and not st.session_state.get("quiz_submitted", False):
        st.header(f"Quiz: {selected_topic}")
        
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
            
            # Simple scoring: 1 point per correct answer if selected, -1 for wrong? 
            # Or just 1 point if ALL correct are selected?
            # User request: "Hvert riktig svar skal gi 1 poeng." 
            # "Gjør det mulig å velge om flere av alternativene skal være korrekt og at man da kan få flere poeng per spørsmål."
            
            # Interpretation: Each correct option selected grants 1 point.
            # What about incorrect options selected? Usually penalizes or gives 0. 
            # Let's assume: +1 for each correct option selected. 0 for others.
            # But wait, if I select ALL options, I get all points? 
            # Usually multiple choice scoring is: (Right - Wrong) or just strict match.
            # "Hvert riktig svar skal gi 1 poeng" -> implies per correct option.
            
            q_score = 0
            q_max = len(correct_indices)
            
            # Let's calculate points
            for idx in user_indices:
                if idx in correct_indices:
                    q_score += 1
                else:
                    # Optional: penalize? User didn't specify penalty. 
                    # But to prevent selecting everything, maybe we should?
                    # For now, let's stick to "Hvert riktig svar skal gi 1 poeng".
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
        category = save_result(
            st.session_state.user_email, 
            st.session_state.user_name, 
            score, 
            total_possible, 
            percentage, 
            selected_topic
        )
        
        st.metric("Din poengsum", f"{score} / {total_possible}", f"{percentage:.1f}%")
        st.success(f"Resultat: {category}")
        
        if st.button("Ta ny quiz"):
            del st.session_state.quiz_data
            del st.session_state.quiz_submitted
            st.rerun()

if __name__ == "__main__":
    main()
