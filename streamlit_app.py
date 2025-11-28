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
    },
    "ar": {
        "title": "مولد الأسئلة متعددة الخيارات",
        "login_google": "تسجيل الدخول باستخدام Google",
        "welcome": "أهلاً بك",
        "logout": "تسجيل الخروج",
        "navigation": "التنقل",
        "module_quiz": "مولد الاختبارات",
        "module_ndla": "محتوى NDLA",
        "settings": "الإعدادات",
        "source": "اختر المصدر:",
        "source_pdf": "Historie på Tvers (كتاب مدرسي)",
        "source_ndla": "NDLA (مورد عبر الإنترنت)",
        "update_topics": "تحديث المواضيع",
        "topics_found": "تم العثور على {} موضوع.",
        "select_topic": "اختر الموضوع",
        "ndla_info": "اختر المواضيع والمقالات من قاعدة بيانات NDLA أدناه.",
        "ndla_expand": "اختر محتوى NDLA",
        "selected_articles": "تم اختيار {} مقال.",
        "no_articles": "لم يتم اختيار أي مقال.",
        "num_questions": "عدد الأسئلة",
        "num_options": "عدد الخيارات",
        "multiple_correct": "إجابات صحيحة متعددة (حد أقصى 2)",
        "generate_btn": "إنشاء الاختبار",
        "analyzing_pdf": "جاري تحليل ملف PDF...",
        "fetching_text": "جاري جلب النص من {}...",
        "error_ndla_select": "يجب عليك اختيار مقال واحد على الأقل من NDLA.",
        "generating": "جاري إنشاء الأسئلة باستخدام الذكاء الاصطناعي...",
        "error_gen": "خطأ في الإنشاء: {}",
        "quiz_header": "اختبار: {}",
        "submit_btn": "إرسال الإجابات",
        "results_header": "النتائج",
        "question": "سؤال",
        "your_answer_correct": "✅ (إجابتك - صحيحة)",
        "your_answer_wrong": "❌ (إجابتك - خاطئة)",
        "correct_answer": "⚠️ (الإجابة الصحيحة)",
        "justification": "التبرير",
        "score": "نتيجتك",
        "result_cat": "النتيجة: {}",
        "download_pdf": "تنزيل النتيجة (PDF)",
        "new_quiz": "بدء اختبار جديد",
        "admin_panel": "إظهار لوحة المسؤول",
        "admin_header": "المسؤول: النتائج (من قاعدة البيانات)",
        "admin_tools": "**أدوات:**\n- [فتح عرض قاعدة بيانات NDLA](http://localhost:8000/ndla_content_viewer.html) (يتطلب خادم محلي)",
        "select_user": "اختر مستخدم للتفاصيل",
        "results_for": "نتائج لـ: {}",
        "total_quizzes": "إجمالي الاختبارات",
        "total_questions": "إجمالي الأسئلة",
        "total_score": "إجمالي النقاط",
        "avg_score": "متوسط النقاط",
        "results_per_topic": "النتائج حسب الموضوع",
        "history": "السجل",
        "download_csv": "تنزيل جميع النتائج (CSV)",
        "no_results": "لم يتم العثور على نتائج بعد.",
        "ndla_viewer_header": "محتوى NDLA",
        "ndla_viewer_info": "تم جلب المحتوى من قاعدة البيانات المحلية بناءً على استخراج NDLA.",
        "ndla_viewer_error": "تعذر تحميل عارض المحتوى: {}",
        "reset_app": "إعادة تعيين التطبيق (تصحيح)"
    },
    "so": {
        "title": "Soo Saaraha Su'aalaha Kala Doorashada",
        "login_google": "Ku gal Google",
        "welcome": "Soo dhawoow",
        "logout": "Ka bax",
        "navigation": "Dhex mar",
        "module_quiz": "Soo Saaraha Imtixaanka",
        "module_ndla": "Nuxurka NDLA",
        "settings": "Dejinta",
        "source": "Dooro Isha:",
        "source_pdf": "Historie på Tvers (Buugga Ardayga)",
        "source_ndla": "NDLA (Khayraadka Online)",
        "update_topics": "Cusbooneysii Mawduucyada",
        "topics_found": "Waxaa la helay {} mawduuc.",
        "select_topic": "Dooro Mawduuc",
        "ndla_info": "Ka dooro mawduucyada iyo maqaallada keydka NDLA hoos.",
        "ndla_expand": "Dooro Nuxurka NDLA",
        "selected_articles": "Waxaa la doortay {} maqaal.",
        "no_articles": "Maqaal lama dooran.",
        "num_questions": "Tirada Su'aalaha",
        "num_options": "Tirada Kala Doorashada",
        "multiple_correct": "Jawaabo Sax ah oo Badan (ugu badnaan 2)",
        "generate_btn": "Samee Imtixaan",
        "analyzing_pdf": "Falanqaynta PDF...",
        "fetching_text": "Ka soo qaadashada qoraalka {}...",
        "error_ndla_select": "Waa inaad doorataa ugu yaraan hal maqaal NDLA.",
        "generating": "Samaynta su'aalaha iyadoo la isticmaalayo AI...",
        "error_gen": "Khalad samaynta: {}",
        "quiz_header": "Imtixaan: {}",
        "submit_btn": "Gudbi Jawaabaha",
        "results_header": "Natiijooyinka",
        "question": "Su'aal",
        "your_answer_correct": "✅ (Jawaabtaada - Sax)",
        "your_answer_wrong": "❌ (Jawaabtaada - Khalad)",
        "correct_answer": "⚠️ (Jawaabta Saxda ah)",
        "justification": "Caddayn",
        "score": "Dhibcahaaga",
        "result_cat": "Natiijo: {}",
        "download_pdf": "Soo dejiso Natiijada (PDF)",
        "new_quiz": "Qaado Imtixaan Cusub",
        "admin_panel": "Muuji Gudiga Maamulka",
        "admin_header": "Maamulka: Natiijooyinka (laga keenay Database)",
        "admin_tools": "**Qalab:**\n- [Fur Muuqaalka Database NDLA](http://localhost:8000/ndla_content_viewer.html) (Wuxuu u baahan yahay server maxalli ah)",
        "select_user": "Dooro Isticmaale Faahfaahin",
        "results_for": "Natiijooyinka: {}",
        "total_quizzes": "Wadarta Imtixaannada",
        "total_questions": "Wadarta Su'aalaha",
        "total_score": "Wadarta Dhibcaha",
        "avg_score": "Celceliska Dhibcaha",
        "results_per_topic": "Natiijooyinka Mawduuc kasta",
        "history": "Taariikhda",
        "download_csv": "Soo dejiso Dhammaan Natiijooyinka (CSV)",
        "no_results": "Natiijooyin lama helin weli.",
        "ndla_viewer_header": "Nuxurka NDLA",
        "ndla_viewer_info": "Nuxurka waxaa laga keenay database-ka maxalliga ah iyadoo lagu saleynayo soo saarista NDLA.",
        "ndla_viewer_error": "Lama soo shubi karo muuqaalka nuxurka: {}",
        "reset_app": "Dib u deji App-ka (Debug)"
    },
    "ti": {
        "title": "ናይ ብዙሕ ምርጫ ሕቶታት መመንጨዊ",
        "login_google": "ብ Google እተው",
        "welcome": "እንቋዕ ብደሓን መጻእኩም",
        "logout": "ውጻእ",
        "navigation": "ምርጫ",
        "module_quiz": "መመንጨዊ ፈተና",
        "module_ndla": "ትሕዝቶ NDLA",
        "settings": "ቅንብራት",
        "source": "ምንጪ ምረጽ:",
        "source_pdf": "Historie på Tvers (መጽሓፍ ተምሃራይ)",
        "source_ndla": "NDLA (ናይ ኦንላይን ምንጪ)",
        "update_topics": "ኣርእስቲ ኣሐድስ",
        "topics_found": "{} ኣርእስቲ ተረኺቡ።",
        "select_topic": "ኣርእስቲ ምረጽ",
        "ndla_info": "ካብ ታሕቲ ዘሎ ቋት ሓበሬታ NDLA ኣርእስትን ዓንቀጻትን ምረጽ።",
        "ndla_expand": "ትሕዝቶ NDLA ምረጽ",
        "selected_articles": "{} ዓንቀጻት ተመሪጹ።",
        "no_articles": "ዝኾነ ዓንቀጽ ኣይተመርጸን።",
        "num_questions": "ብዝሒ ሕቶታት",
        "num_options": "ብዝሒ ምርጫታት",
        "multiple_correct": "ብዙሕ ቅኑዕ መልሲ (ብዝበዝሐ 2)",
        "generate_btn": "ፈተና ፍጠር",
        "analyzing_pdf": "PDF ይምርምር ኣሎ...",
        "fetching_text": "ጽሑፍ ካብ {} የውጽእ ኣሎ...",
        "error_ndla_select": "ካብ NDLA እንተወሓደ ሓደ ዓንቀጽ ክትመርጽ ኣለካ።",
        "generating": "ብ AI ሕቶታት ይፈጥር ኣሎ...",
        "error_gen": "ጌጋ ኣብ ምፍጣር: {}",
        "quiz_header": "ፈተና: {}",
        "submit_btn": "መልሲ ኣረክብ",
        "results_header": "ውጽኢት",
        "question": "ሕቶ",
        "your_answer_correct": "✅ (መልስኻ - ቅኑዕ)",
        "your_answer_wrong": "❌ (መልስኻ - ጌጋ)",
        "correct_answer": "⚠️ (ቅኑዕ መልሲ)",
        "justification": "መብርሂ",
        "score": "ውጽኢትካ",
        "result_cat": "ውጽኢት: {}",
        "download_pdf": "ውጽኢት ኣውርድ (PDF)",
        "new_quiz": "ሓድሽ ፈተና ውሰድ",
        "admin_panel": "ናይ ኣመሓዳሪ ፓነል ኣርእይ",
        "admin_header": "ኣመሓዳሪ: ውጽኢት (ካብ ቋት ሓበሬታ)",
        "admin_tools": "**መሳርሒታት:**\n- [ናይ NDLA ቋት ሓበሬታ ርኣይ](http://localhost:8000/ndla_content_viewer.html) (Local server የድሊ)",
        "select_user": "ንዝርዝር ተጠቃሚ ምረጽ",
        "results_for": "ውጽኢት ናይ: {}",
        "total_quizzes": "ጠቕላላ ፈተናታት",
        "total_questions": "ጠቕላላ ሕቶታት",
        "total_score": "ጠቕላላ ነጥቢ",
        "avg_score": "ማእከላይ ነጥቢ",
        "results_per_topic": "ውጽኢት ብኣርእስቲ",
        "history": "ታሪኽ",
        "download_csv": "ኩሉ ውጽኢት ኣውርድ (CSV)",
        "no_results": "ክሳብ ሕጂ ዝኾነ ውጽኢት ኣይተረኽበን።",
        "ndla_viewer_header": "ትሕዝቶ NDLA",
        "ndla_viewer_info": "ትሕዝቶ ካብቲ ብ NDLA ዝተረኽበ ናይ ውሽጢ ቋት ሓበሬታ እዩ ተወሲዱ።",
        "ndla_viewer_error": "መራእዪ ትሕዝቶ ክጽዕን ኣይከኣለን: {}",
        "reset_app": "App ሪሰት ግበር (Debug)"
    }
}

def get_text(key, *args):
    lang = st.session_state.get("language", "no")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["no"]).get(key, key)
    if args:
        return text.format(*args)
    return text

def apply_custom_css():
    # Check for Arabic to apply RTL
    lang = st.session_state.get("language")
    is_rtl = lang == "ar"
    direction = "rtl" if is_rtl else "ltr"
    align = "right" if is_rtl else "left"
    
    st.markdown(f"""
        <style>
        /* Main Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap'); /* Arabic Font */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;700&display=swap'); /* Tigrinya Font */
        
        html, body, [class*="css"] {{
            font-family: 'Inter', 'Cairo', 'Noto Sans Ethiopic', sans-serif;
            direction: {direction};
        }}
        
        /* Background - Dark */
        .stApp {{
            background-color: #0e1117;
            color: #fafafa;
        }}
        
        /* Sidebar - Slightly lighter dark */
        [data-testid="stSidebar"] {{
            background-color: #262730;
            border-right: 1px solid #333;
            min-width: 500px; /* Widen sidebar even more */
            max-width: 800px;
        }}
        
        /* Headers */
        h1, h2, h3 {{
            font-weight: 600;
            color: #ffffff !important;
            text-align: {align};
        }}
        
        /* Buttons */
        .stButton button {{
            background-color: #4c4cff; /* Accent color */
            color: white !important;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        .stButton button:hover {{
            background-color: #3b3bff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}
        
        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
            border-radius: 8px;
            border: 1px solid #444;
            background-color: #1a1c24;
            color: white;
            direction: {direction};
        }}
        
        /* Cards/Containers */
        .css-1r6slb0 {{
            background-color: #1a1c24;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        /* Links */
        a {{
            color: #4c4cff !important;
        }}
        
        /* Checkbox/Radio text */
        .stCheckbox label, .stRadio label {{
            color: #fafafa;
        }}
        </style>
    """, unsafe_allow_html=True)

# ... (render_ndla_viewer and render_quiz_generator unchanged) ...

def main():
    # Initialize Language FIRST
    if "language" not in st.session_state:
        st.session_state.language = "no"

    apply_custom_css()

    # --- Authentication (MOVED TO TOP) ---
    if "google" not in st.secrets:
        st.error("Google secrets not found in .streamlit/secrets.toml")
        st.stop()
        
    # Read and clean secrets
    client_id = st.secrets["google"]["client_id"].strip()
    client_secret = st.secrets["google"]["client_secret"].strip()
    redirect_uri = st.secrets["google"]["redirect_uri"].strip()
    
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
        state = query_params.get("state")
        
        # Handle list if necessary
        if isinstance(state, list):
            state = state[0]
        
        if code:
            # Restore language from state if valid
            if state and state in ["no", "en", "ar", "so", "ti"]:
                st.session_state.language = state
                # We can safely set this here because the widget hasn't been rendered yet!
                st.session_state["lang_selector"] = state
                st.session_state["lang_selector_login"] = state
                
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
            # We show this INSTEAD of the main app if not logged in
            
            # Show Language Selector on Login Screen too!
            st.image(LOGO_URL, width=150)
            st.title(get_text("title"))
            
            lang_options = {"no": "🇳🇴 Norsk", "en": "🇬🇧 English", "ar": "🇸🇦 العربية", "so": "🇸🇴 Soomaali", "ti": "🇪🇷 ትግርኛ"}
            selected_lang = st.radio(
                "Language / Språk / لغة", 
                options=list(lang_options.keys()), 
                format_func=lambda x: lang_options[x],
                index=0 if st.session_state.language == "no" else (1 if st.session_state.language == "en" else (2 if st.session_state.language == "ar" else (3 if st.session_state.language == "so" else 4))),
                key="lang_selector_login",
                horizontal=True
            )
            
            if selected_lang != st.session_state.language:
                st.session_state.language = selected_lang
                st.rerun()
            
            import urllib.parse
            
            scope = "openid email profile"
            
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": scope,
                "access_type": "offline",
                "prompt": "consent",
                "state": st.session_state.language # Pass language as state
            }
            
            # Use quote_via=urllib.parse.quote to get %20 instead of + for spaces
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
            
            st.markdown(f'''
                <br>
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

    # --- Main App (Only reached if logged in) ---
    
    # Logo in Sidebar
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.title(get_text("title"))
    
    # Language Selector (Sidebar)
    lang_options = {"no": "🇳🇴 Norsk", "en": "🇬🇧 English", "ar": "🇸🇦 العربية", "so": "🇸🇴 Soomaali", "ti": "🇪🇷 ትግርኛ"}
    selected_lang = st.sidebar.radio(
        "Language / Språk / لغة", 
        options=list(lang_options.keys()), 
        format_func=lambda x: lang_options[x],
        index=0 if st.session_state.language == "no" else (1 if st.session_state.language == "en" else (2 if st.session_state.language == "ar" else (3 if st.session_state.language == "so" else 4))),
        key="lang_selector"
    )
    
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

if __name__ == "__main__":
    main()
