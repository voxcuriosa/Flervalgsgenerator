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
st.set_page_config(page_title="HPT Quiz Generator", layout="wide", initial_sidebar_state="expanded")

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
    },
    "uk": {
        "title": "Генератор тестів з варіантами відповідей",
        "login_google": "Увійти через Google",
        "welcome": "Ласкаво просимо",
        "logout": "Вийти",
        "navigation": "Навігація",
        "module_quiz": "Генератор тестів",
        "module_ndla": "Контент NDLA",
        "settings": "Налаштування",
        "source": "Оберіть джерело:",
        "source_pdf": "Historie på Tvers (Підручник)",
        "source_ndla": "NDLA (Онлайн ресурс)",
        "update_topics": "Оновити теми",
        "topics_found": "Знайдено {} тем.",
        "select_topic": "Оберіть тему",
        "ndla_info": "Оберіть теми та статті з бази даних NDLA нижче.",
        "ndla_expand": "Оберіть контент NDLA",
        "selected_articles": "Обрано {} статей.",
        "no_articles": "Статті не обрано.",
        "num_questions": "Кількість питань",
        "num_options": "Кількість варіантів",
        "multiple_correct": "Кілька правильних відповідей (макс. 2)",
        "generate_btn": "Згенерувати тест",
        "analyzing_pdf": "Аналіз PDF...",
        "fetching_text": "Отримання тексту з {}...",
        "error_ndla_select": "Ви повинні обрати хоча б одну статтю з NDLA.",
        "generating": "Генерація питань за допомогою ШІ...",
        "error_gen": "Помилка генерації: {}",
        "quiz_header": "Тест: {}",
        "submit_btn": "Надіслати відповіді",
        "results_header": "Результати",
        "question": "Питання",
        "your_answer_correct": "✅ (Ваша відповідь - Правильно)",
        "your_answer_wrong": "❌ (Ваша відповідь - Неправильно)",
        "correct_answer": "⚠️ (Правильна відповідь)",
        "justification": "Обґрунтування",
        "score": "Ваш результат",
        "result_cat": "Результат: {}",
        "download_pdf": "Завантажити результат (PDF)",
        "new_quiz": "Пройти новий тест",
        "admin_panel": "Показати панель адміністратора",
        "admin_header": "Адмін: Результати (з бази даних)",
        "admin_tools": "**Інструменти:**\n- [Відкрити перегляд бази даних NDLA](http://localhost:8000/ndla_content_viewer.html) (Потрібен локальний сервер)",
        "select_user": "Оберіть користувача для деталей",
        "results_for": "Результати для: {}",
        "total_quizzes": "Всього тестів",
        "total_questions": "Всього питань",
        "total_score": "Загальний бал",
        "avg_score": "Середній бал",
        "results_per_topic": "Результати за темами",
        "history": "Історія",
        "download_csv": "Завантажити всі результати (CSV)",
        "no_results": "Результатів поки не знайдено.",
        "ndla_viewer_header": "Контент NDLA",
        "ndla_viewer_info": "Контент отримано з локальної бази даних на основі скрапінгу NDLA.",
        "ndla_viewer_error": "Не вдалося завантажити переглядач контенту: {}",
        "reset_app": "Скинути додаток (Debug)"
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
        }}
        
        /* Desktop only sidebar width */
        @media (min-width: 768px) {{
            [data-testid="stSidebar"] {{
                min-width: 500px;
                max-width: 800px;
            }}
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
        /* Sidebar Toggle Button (Mobile) */
        /* Sidebar Toggle Button (Mobile) */
        [data-testid="stSidebarCollapsedControl"] {{
            background-color: #262730;
            border: 1px solid #4c4cff;
            border-radius: 5px;
            padding: 5px;
            color: white;
        }}
        
        [data-testid="stSidebarCollapsedControl"] svg {{
            height: 30px !important;
            width: 30px !important;
        }}
        
        /* Make the header toolbar background visible on mobile to contrast the button */
        header[data-testid="stHeader"] {{
            background-color: #0e1117;
        }}
        </style>
    """, unsafe_allow_html=True)

# ... (render_ndla_viewer and render_quiz_generator unchanged) ...

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
            
            # --- 1. Settings (Max Questions) ---
            st.info("⚙️ **Innstillinger**")
            
            # Max Question Limit Setting
            from storage import get_setting, save_setting
            
            current_max_limit = int(get_setting("max_question_limit", 20))
            
            new_max_limit = st.slider(
                "Maksimalt antall spørsmål (standardverdi for nye quizer)",
                min_value=20,
                max_value=100,
                value=current_max_limit,
                step=5,
                key="admin_max_limit"
            )
            
            if new_max_limit != current_max_limit:
                if save_setting("max_question_limit", new_max_limit):
                    st.success(f"Lagret ny grense: {new_max_limit}")
                    # Rerun to update the quiz generator slider immediately
                    st.rerun()
                else:
                    st.error("Kunne ikke lagre innstillingen.")
            
            st.divider()

            # --- 2. Quiz Results Section ---
            st.markdown(get_text("admin_tools"))
            
            # Import the new function
            from storage import get_all_results, delete_results
            
            # Lazy Loading
            if "load_results" not in st.session_state:
                st.session_state.load_results = False
                
            if not st.session_state.load_results:
                if st.button("Last inn resultater"):
                    st.session_state.load_results = True
                    st.rerun()
            else:
                if st.button("Skjul resultater"):
                    st.session_state.load_results = False
                    st.rerun()
                    
                df = get_all_results()
                
                if not df.empty:
                    # Summary Metrics
                    total_quizzes = len(df)
                    unique_users = df['user_email'].nunique()
                    avg_score_all = df['percentage'].mean()
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Totalt antall quizer", total_quizzes)
                    m2.metric("Unike brukere", unique_users)
                    m3.metric("Snittscore (alle)", f"{avg_score_all:.1f}%")
                    
                    st.write("### Detaljerte resultater")
                    
                    # Filter by user
                    users = ["Alle"] + list(df['user_email'].unique())
                    selected_user = st.selectbox("Filtrer på bruker:", users)
                    
                    if selected_user != "Alle":
                        user_df = df[df['user_email'] == selected_user]
                        
                        # User specific actions
                        col_u1, col_u2 = st.columns([0.8, 0.2])
                        with col_u1:
                            st.write(f"Viser {len(user_df)} resultater for {selected_user}")
                        with col_u2:
                            if st.button("Slett alle for bruker", type="primary", key=f"del_user_{selected_user}"):
                                if delete_results(user_email=selected_user):
                                    st.success(f"Slettet alle resultater for {selected_user}")
                                    st.rerun()
                                else:
                                    st.error("Kunne ikke slette resultater.")
                        
                        # Display user results with delete buttons per row
                        st.dataframe(user_df[['timestamp', 'topic', 'score', 'total', 'percentage', 'category']], hide_index=True)
                        
                        # Option to delete specific test?
                        # Let's show a list of recent tests with delete buttons
                        st.write("#### Siste tester (Slett enkelttester)")
                        
                        # Collect IDs to delete
                        delete_ids = []
                        
                        # Header
                        h1, h2, h3, h4, h5 = st.columns([0.5, 2, 2, 1, 1])
                        h1.write("**Velg**")
                        h2.write("**Dato**")
                        h3.write("**Emne**")
                        h4.write("**Score**")
                        h5.write("**Prosent**")
                        
                        for index, row in user_df.iterrows():
                            c1, c2, c3, c4, c5 = st.columns([0.5, 2, 2, 1, 1])
                            # Use a unique key for each checkbox
                            if c1.checkbox("", key=f"sel_res_{row['id']}"):
                                delete_ids.append(row['id'])
                            c2.text(row['timestamp'])
                            c3.text(row['topic'])
                            c4.text(f"{row['score']}/{row['total']}")
                            c5.text(f"{row['percentage']}%")
                            
                        if delete_ids:
                            st.write("")
                            if st.button(f"Slett {len(delete_ids)} valgte tester", type="primary", key="bulk_delete_btn"):
                                if delete_results(result_ids=delete_ids):
                                    st.success(f"Slettet {len(delete_ids)} tester!")
                                    st.rerun()
                        
                    else:
                        # Show all results
                        st.dataframe(df)
                        
                        # Delete all results option (Dangerous!)
                        with st.expander("Faresone"):
                            if st.button("Slett ALLE resultater i databasen", type="primary"):
                                st.warning("Dette er ikke implementert for sikkerhets skyld. Kontakt utvikler.")
                    
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
            
            st.divider()

            # --- 3. Content Update Section (Moved to Bottom) ---
            st.info("🛠️ **Verktøy for innholdsoppdatering**")
            
            st.write("Her kan du hente siste versjon av innholdet fra NDLA. Velg fag og emner du vil oppdatere.")
            
            # Select Subject
            update_subject = st.selectbox("Velg fag", ["Historie vg2", "Historie vg3"], key="update_subject")
            
            # Fetch available topics for this subject
            from scrape_ndla import get_subject_topics, update_topic
            
            with st.spinner(f"Henter emner for {update_subject}..."):
                available_topics = get_subject_topics(update_subject)
                
            if available_topics:
                # Create a form/list for selection
                st.write("Velg emner å oppdaterte:")
                
                selected_nodes = []
                
                # "Select All" option for everything
                select_all_global = st.checkbox("Velg ALT innhold (alle emner og underemner)")
                
                for topic in available_topics:
                    # Top level topic
                    with st.expander(f"{topic['name']}", expanded=False):
                        # Option to select the entire top-level topic
                        col1, col2 = st.columns([0.05, 0.95])
                        with col1:
                            is_parent_selected = st.checkbox("", key=f"parent_{topic['id']}", value=select_all_global)
                        with col2:
                            st.markdown(f"**Oppdater hele '{topic['name']}'** (inkludert alle underemner)")
                        
                        # Subtopics
                        if topic['children']:
                            st.markdown("Eller velg spesifikke underemner:")
                            for sub in topic['children']:
                                is_sub_selected = st.checkbox(sub['name'], key=f"sub_{sub['id']}", value=is_parent_selected or select_all_global)
                                
                                if is_sub_selected:
                                    selected_nodes.append(sub)
                        
                        if is_parent_selected:
                            selected_nodes.append(topic)

                # Deduplicate selected nodes by ID
                unique_nodes = {node['id']: node for node in selected_nodes}.values()
                
                st.write("") # Spacing
                
                if st.button(f"Oppdater {len(unique_nodes)} valgte emner", type="primary"):
                    if unique_nodes:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total = len(unique_nodes)
                        success_count = 0
                        
                        for i, node in enumerate(unique_nodes):
                            status_text.text(f"Oppdaterer: {node['name']}...")
                            if update_topic(update_subject, node['name'], node['id']):
                                success_count += 1
                            progress_bar.progress((i + 1) / total)
                            
                        status_text.text("Ferdig!")
                        st.success(f"Oppdatering fullført! {success_count} av {total} emner ble oppdatert.")
                        
                        # Regenerate HTML
                        with st.spinner("Oppdaterer visning..."):
                            import subprocess
                            subprocess.run(["python3", "generate_html_viewer.py"])
                        st.info("HTML-visning er oppdatert.")
                        
                    else:
                        st.warning("Ingen emner valgt.")
            else:
                st.error("Kunne ikke hente emner fra NDLA. Sjekk internettforbindelsen.")
            
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
    
    # Get configured max limit
    from storage import get_setting
    max_q_limit = int(get_setting("max_question_limit", 20))
    
    num_questions = st.sidebar.slider(get_text("num_questions"), 1, max_q_limit, min(20, max_q_limit))
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
            if state and state in ["no", "en", "ar", "so", "ti", "uk"]:
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
            
            lang_options = {
                "no": "🇳🇴 Norsk", 
                "en": "🇬🇧 English", 
                "ar": "🇸🇦 العربية", 
                "so": "🇸🇴 Soomaali", 
                "ti": "🇪🇷 ትግርኛ", 
                "uk": "🇺🇦 Українська",
                "th": "🇹🇭 ไทย"
            }
            selected_lang = st.radio(
                "Language / Språk / لغة", 
                options=list(lang_options.keys()), 
                format_func=lambda x: lang_options[x],
                index=0 if st.session_state.language == "no" else (1 if st.session_state.language == "en" else (2 if st.session_state.language == "ar" else (3 if st.session_state.language == "so" else (4 if st.session_state.language == "ti" else (5 if st.session_state.language == "uk" else 6))))),
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
    
    # Language Selector in Sidebar
    st.sidebar.markdown(f"**{get_text('language')}**")
    lang_options = {
        "no": "🇳🇴 Norsk", 
        "en": "🇬🇧 English", 
        "ar": "🇸🇦 العربية", 
        "so": "🇸🇴 Soomaali", 
        "ti": "🇪🇷 ትግርኛ", 
        "uk": "🇺🇦 Українська",
        "th": "🇹🇭 ไทย"
    }
    
    # Use a callback to update state immediately
    def update_lang():
        st.session_state.language = st.session_state.lang_selector
        st.rerun()
        
    st.sidebar.radio(
        "Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=0 if st.session_state.language == "no" else (1 if st.session_state.language == "en" else (2 if st.session_state.language == "ar" else (3 if st.session_state.language == "so" else (4 if st.session_state.language == "ti" else (5 if st.session_state.language == "uk" else 6))))),
        key="lang_selector",
        label_visibility="collapsed",
        on_change=update_lang
    )

    if st.sidebar.button(get_text("reset_app")):
        for key in list(st.session_state.keys()):
            if key != "language": # Keep language
                del st.session_state[key]
        st.rerun()

    st.write(f"{get_text('welcome')}, {st.session_state.get('user_name', '')}!")
    
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
