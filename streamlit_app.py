import streamlit as st # Force reload v2.2.4 fix
import pandas as pd
import os
from quiz_generator import generate_quiz
from pdf_processor import get_topics, extract_text_by_topic
from storage import save_result, get_content_hierarchy
from pdf_generator import generate_quiz_pdf
from ndla_selector import render_ndla_selector
from generate_html_viewer import generate_html
from docx_generator import generate_docx
import streamlit_oauth as oauth
import asyncio
import streamlit.components.v1 as components
import streamlit.components.v1 as components
import streamlit.components.v1 as components
import extra_streamlit_components as stx
import requests
import json

# Page Config
st.set_page_config(page_title="Flervalgsgenerator", page_icon="📝", layout="wide", initial_sidebar_state="expanded")

# Constants
PDF_FILES = ["HPT.pdf", "HPTx.pdf"]
HTML_VIEWER_PATH = "ndla_content_viewer.html"
LOGO_URL = "logo.png"
ADMINS = ["borchgrevink@gmail.com", "hanslaa@gmail.com", "nilsnaas@gmail.com"]

# Translations
TRANSLATIONS = {
    "no": {
        "title": "Generator for flervalgsoppgaver",
        "language": "Språk",
        "login_google": "Logg inn med Google",
        "welcome": "Velkommen",
        "logout": "Logg ut",
        "navigation": "Navigasjon",
        "home": "Hjem",
        "my_history": "Min Historikk",
        "module_quiz": "Quiz-generator",
        "module_ndla": "NDLA Fagstoff",
        "settings": "Kilde til quiz",
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
        "generating": "Generer spørsmål med AI (OpenAI GPT-4o)...",
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
        "admin_tools": "**Verktøy:**\n- [Åpne NDLA Database-visning](ndla_content_viewer.html) (Krever at server kjører lokalt)",
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
        "ndla_viewer_error": "Kunne ikke laste innholdsvisning: {}",
        "reset_app": "Nullstill app (Debug)",
        "url_input_label": "URL til nettside",
        "fetch_and_gen_btn": "Hent innhold og generer quiz",
        "paste_url_warning": "Du må lime inn en URL først.",
        "fetch_content_spinner": "Henter innhold fra nettside...",
        "no_text_found": "Fant ingen tekst på siden.",
        "paste_urls_info": "Lim inn URL-er til artikler du vil generere spørsmål fra. Du kan legge til flere URL-er ved å trykke på Enter mellom hver.",
        "urls_input_label": "URL-er (én per linje):",
        "fetch_urls_btn": "Hent innhold fra {} URL-er",
        "welcome_message": """**Velkommen til Flervalgsgeneratoren!**

Dette verktøyet er utviklet for å gjøre det enkelt og effektivt å lage gode flervalgsoppgaver. Du kan hente fagstoff direkte fra læreboka *Historie på tvers* eller fra NDLA sine omfattende ressurser.

Du har også stor fleksibilitet til å bruke eget materiale:
*   Lim inn tekst fra nettsider
*   Last opp filer (PDF, PowerPoint, Word)

Du styrer selv vanskelighetsgraden ved å velge antall spørsmål, svaralternativer og hvor mange riktige svar som skal genereres.

I tillegg fungerer appen som en leser for NDLA-fagstoff, slik at du kan bla i og vurdere innholdet før du lager oppgaver.

_Lykke til med arbeidet!_

PS: Oppdager du feil eller har forslag? Ta kontakt på borchgrevink@gmail.com"""
    },
    "nn": {
        "title": "Generator for fleirvalsoppgåver",
        "language": "Språk",
        "login_google": "Logg inn med Google",
        "welcome": "Velkomen",
        "logout": "Logg ut",
        "navigation": "Navigasjon",
        "home": "Heim",
        "my_history": "Min Historikk",
        "module_quiz": "Quiz-generator",
        "module_ndla": "NDLA Fagstoff",
        "settings": "Kjelde til quiz",
        "source": "Vel kjelde:",
        "source_pdf": "Historie på Tvers (Lærebok)",
        "source_ndla": "NDLA (Nettressurs)",
        "update_topics": "Oppdater emne",
        "topics_found": "Fann {} emne.",
        "select_topic": "Vel emne",
        "ndla_info": "Vel emne og artiklar frå NDLA-databasen nedanfor.",
        "ndla_expand": "Vel NDLA-innhald",
        "selected_articles": "Valt {} artiklar.",
        "no_articles": "Ingen artiklar valde.",
        "num_questions": "Tal på spørsmål",
        "num_options": "Tal på svaralternativ",
        "multiple_correct": "Fleire rette svar (maks 2)",
        "generate_btn": "Generer quiz",
        "analyzing_pdf": "Analyserer PDF...",
        "fetching_text": "Hentar tekst frå {}...",
        "error_ndla_select": "Du må velje minst éin artikkel frå NDLA.",
        "generating": "Genererer spørsmål med AI (OpenAI GPT-4o)...",
        "error_gen": "Feil under generering: {}",
        "quiz_header": "Quiz: {}",
        "submit_btn": "Lever svar",
        "results_header": "Resultat",
        "question": "Spørsmål",
        "your_answer_correct": "✅ (Ditt svar - Rett)",
        "your_answer_wrong": "❌ (Ditt svar - Feil)",
        "correct_answer": "⚠️ (Rett svar)",
        "justification": "Grunngiving",
        "score": "Din poengsum",
        "result_cat": "Resultat: {}",
        "download_pdf": "Last ned resultat (PDF)",
        "new_quiz": "Ta ny quiz",
        "admin_panel": "Vis admin-panel",
        "admin_header": "Admin: Resultat (frå Database)",
        "admin_tools": "**Verktøy:**\n- [Opne NDLA Database-visning](http://localhost:8000/ndla_content_viewer.html) (Krev lokal server)",
        "select_user": "Vel brukar for detaljar",
        "results_for": "Resultat for: {}",
        "total_quizzes": "Totalt tal på quizar",
        "total_questions": "Totalt tal på spørsmål",
        "total_score": "Total poengsum",
        "avg_score": "Gjennomsnittleg poengsum",
        "results_per_topic": "Resultat per emne",
        "history": "Historikk",
        "download_csv": "Last ned alle resultat (CSV)",
        "no_results": "Ingen resultat funne enno.",
        "ndla_viewer_header": "NDLA Innhald",
        "ndla_viewer_info": "Innhald henta frå lokal database basert på NDLA-scraping.",
        "ndla_viewer_error": "Kunne ikkje laste innhaldsvisar: {}",
        "reset_app": "Nullstill app (Debug)",
        "url_input_label": "URL til nettside",
        "fetch_and_gen_btn": "Hent innhald og generer quiz",
        "paste_url_warning": "Du må lime inn ein URL først.",
        "fetch_content_spinner": "Hentar innhald frå nettside...",
        "no_text_found": "Fann ingen tekst på sida.",
        "paste_urls_info": "Lim inn URL-ar til artiklar du vil generere spørsmål frå. Du kan leggje til fleire URL-ar ved å trykkje på Enter mellom kvar.",
        "urls_input_label": "URL-ar (éin per linje):",
        "fetch_urls_btn": "Hent innhald frå {} URL-ar",
        "welcome_message": """**Velkomen til Fleirvalgsgeneratoren!**

Dette verktøyet er utvikla for å gjere det enkelt og effektivt å lage gode fleirvalsoppgåver. Du kan hente fagstoff direkte frå læreboka *Historie på tvers* eller frå NDLA sine omfattande ressursar.

Du har òg stor fleksibilitet til å bruke eige materiale:
*   Lim inn tekst frå nettsider
*   Last opp filer (PDF, PowerPoint, Word)

Du styrer sjølv vanskelegheitsgraden ved å velje tal på spørsmål, svaralternativ og kor mange rette svar som skal genererast.

I tillegg fungerer appen som ein lesar for NDLA-fagstoff, slik at du kan bla i og vurdere innhaldet før du lagar oppgåver.

_Lukke til med arbeidet!_

PS: Oppdagar du feil eller har forslag? Ta kontakt på borchgrevink@gmail.com"""
    },
    "en": {
        "title": "Multiple Choice Generator",
        "language": "Language",
        "login_google": "Login with Google",
        "welcome": "Welcome",
        "logout": "Log out",
        "navigation": "Navigation",
        "home": "Home",
        "my_history": "My History",
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
        "generating": "Generating questions with AI (OpenAI GPT-4o)...",
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
        "reset_app": "Reset App (Debug)",
        "url_input_label": "URL to website",
        "fetch_and_gen_btn": "Fetch content and generate quiz",
        "paste_url_warning": "You must paste a URL first.",
        "fetch_content_spinner": "Fetching content from website...",
        "no_text_found": "No text found on page.",
        "paste_urls_info": "Paste URLs to articles you want to generate questions from. You can add multiple URLs by pressing Enter between each.",
        "urls_input_label": "URLs (one per line):",
        "fetch_urls_btn": "Fetch content from {} URLs",
        "welcome_message": """**Welcome to the Multiple Choice Generator!**

This tool is designed to make it easy and efficient to create good multiple-choice questions. You can fetch subject material directly from the textbook *Historie på tvers* or from NDLA's extensive resources.

You also have great flexibility to use your own material:
*   Paste text from websites
*   Upload files (PDF, PowerPoint, Word)

You control the difficulty level yourself by choosing the number of questions, answer options, and how many correct answers to generate.

In addition, the app functions as a reader for NDLA subject material, allowing you to browse and evaluate the content before creating questions.

_Good luck with your work!_

PS: Discover errors or have suggestions? Contact borchgrevink@gmail.com"""
    },
    "ar": {
        "title": "مولد الأسئلة متعددة الخيارات",
        "login_google": "تسجيل الدخول باستخدام Google",
        "welcome": "أهلاً بك",
        "logout": "تسجيل الخروج",
        "navigation": "التنقل",
        "home": "الرئيسية",
        "my_history": "تاريخي",
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
        "generating": "جاري إنشاء الأسئلة باستخدام الذكاء الاصطناعي (OpenAI GPT-4o)...",
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
        "reset_app": "إعادة تعيين التطبيق (تصحيح)",
        "url_input_label": "URL للموقع",
        "fetch_and_gen_btn": "جلب المحتوى وإنشاء اختبار",
        "paste_url_warning": "يجب عليك لصق عنوان URL أولاً.",
        "fetch_content_spinner": "جاري جلب المحتوى من الموقع...",
        "no_text_found": "لم يتم العثور على نص في الصفحة.",
        "paste_urls_info": "الصق عناوين URL للمقالات التي تريد إنشاء أسئلة منها. يمكنك إضافة عناوين URL متعددة بالضغط على Enter بين كل منها.",
        "urls_input_label": "عناوين URL (واحد في كل سطر):",
        "fetch_urls_btn": "جلب المحتوى من {} عناوين URL",
        "welcome_message": """**مرحبًا بك في مولد الأسئلة متعددة الخيارات!**

تم تطوير هذه الأداة لتسهيل إنشاء أسئلة متعددة الخيارات جيدة وبكفاءة. يمكنك جلب المواد الدراسية مباشرة من الكتاب المدرسي *Historie på tvers* أو من موارد NDLA الشاملة.

لديك أيضًا مرونة كبيرة لاستخدام المواد الخاصة بك:
*   لصق النص من مواقع الويب
*   تحميل الملفات (PDF، PowerPoint، Word)

أنت تتحكم في مستوى الصعوبة بنفسك عن طريق اختيار عدد الأسئلة وخيارات الإجابة وعدد الإجابات الصحيحة التي سيتم إنشاؤها.

بالإضافة إلى ذلك، يعمل التطبيق كقارئ لمواد NDLA الدراسية، بحيث يمكنك تصفح المحتوى وتقييمه قبل إنشاء الأسئلة.

_حظًا سعيدًا في عملك!_

ملاحظة: هل اكتشفت أخطاء أو لديك اقتراحات؟ تواصل معنا على borchgrevink@gmail.com"""
    },
    "so": {
        "title": "Soo Saaraha Su'aalaha Kala Doorashada",
        "login_google": "Ku gal Google",
        "welcome": "Soo dhawoow",
        "logout": "Ka bax",
        "navigation": "Dhex mar",
        "home": "Hoyga",
        "my_history": "Taariikhdayda",
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
        "generating": "Samaynta su'aalaha iyadoo la isticmaalayo AI (OpenAI GPT-4o)...",
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
        "reset_app": "Dib u deji App-ka (Debug)",
        "url_input_label": "URL-ka websaydhka",
        "fetch_and_gen_btn": "Keen nuxurka oo samee imtixaan",
        "paste_url_warning": "Waa inaad marka hore dhejisaa URL.",
        "fetch_content_spinner": "Ka keenaya nuxurka websaydhka...",
        "no_text_found": "Qoraal lagama helin bogga.",
        "paste_urls_info": "Dheji URL-yada maqaallada aad rabto inaad su'aalo ka sameyso. Waxaad ku dari kartaa URL-yo badan adigoo riixaya Enter inta u dhaxaysa.",
        "urls_input_label": "URL-yada (midkiiba hal sadar):",
        "fetch_urls_btn": "Ka keen nuxurka {} URL-yo",
        "welcome_message": """**Ku soo dhawoow Soo-saaraha Su'aalaha Kala-doorashada!**

Qalabkan waxaa loo sameeyay inuu fududeeyo oo uu waxtar u yeesho abuurista su'aalo kala-doorasho oo wanaagsan. Waxaad si toos ah uga soo qaadan kartaa agabka maadada buugga *Historie på tvers* ama kheyraadka ballaaran ee NDLA.

Waxaad sidoo kale leedahay dabacsanaan weyn oo aad ku isticmaali karto agabkaaga:
*   Ka soo dheji qoraalka websaydhada
*   Soo rar faylasha (PDF, PowerPoint, Word)

Adiga ayaa xakameynaya heerka adkaanta adigoo dooranaya tirada su'aalaha, xulashooyinka jawaabaha iyo inta jawaabood ee saxda ah ee la soo saarayo.

Intaa waxaa dheer, app-ku wuxuu u shaqeeyaa sidii akhriste agabka maadada NDLA, si aad u baarto oo aad u qiimeyso nuxurka ka hor inta aadan abuurin su'aalo.

_Nasiib wacan shaqadaada!_

PS: Ma aragtay khaladaad mise waxaad haysaa soo jeedin? Kala xiriir borchgrevink@gmail.com"""
    },
    "ti": {
        "title": "ናይ ብዙሕ ምርጫ ሕቶታት መመንጨዊ",
        "login_google": "ብ Google እተው",
        "welcome": "እንቋዕ ብደሓን መጻእኩም",
        "logout": "ውጻእ",
        "navigation": "ምርጫ",
        "home": "ገዛ",
        "my_history": "ናይ ታሪኽ",
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
        "generating": "ብ AI ሕቶታት ይፈጥር ኣሎ (OpenAI GPT-4o)...",
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
        "ndla_viewer_info": "Innholdet hentes fra lokal database basert på NDLA-skraping.",
        "ndla_viewer_error": "Kunne ikke laste innholdsvisning: {}",
        "reset_app": "Nullstill app (Debug)",
        "url_input_label": "URL ናብ መርበብ ሓበሬታ",
        "fetch_and_gen_btn": "ትሕዝቶ ኣምጽእ እሞ ፈተና ፍጠር",
        "paste_url_warning": "ቅድም URL ክትለጥፍ ኣለካ።",
        "fetch_content_spinner": "ትሕዝቶ ካብ መርበብ ሓበሬታ የውጽእ ኣሎ...",
        "no_text_found": "ኣብቲ ገጽ ዝኾነ ጽሑፍ ኣይተረኽበን።",
        "paste_urls_info": "URL ናይቶም ሕቶታት ክትፈጥረሎም እትደሊ ዓንቀጻት ለጥፍ። ኣብ መንጎ ነፍሲ ወከፍ Enter ብምርጋጽ ብዙሓት URL ክትውስኽ ትኽእል ኢኻ።",
        "urls_input_label": "URLs (ሓደ ኣብ ነፍሲ ወከፍ መስመር):",
        "fetch_urls_btn": "ትሕዝቶ ካብ {} URLs ኣምጽእ",
        "welcome_message": """**እንቋዕ ናብ መውለዲ ብዙሕ ምርጫ ብደሓን መጻእኩም!**

እዚ መሳርሒ ጽቡቕ ናይ ብዙሕ ምርጫ ሕቶታት ብቐሊሉን ብብቕዓትን ንምድላው ዝተዳለወ እዩ። ናይ ትምህርቲ ጽሑፍ ብቐጥታ ካብ መጽሓፍ *Historie på tvers* ወይ ካብ ሰፊሕ ጸጋታት NDLA ከተምጽኡ ትኽእሉ ኢኹም።

ናይ ገዛእ ርእስኹም ጽሑፍ ንምጥቃም እውን ዓቢ ተዓጻጻፍነት ኣለኩም:
*   ጽሑፍ ካብ መርበብ ሓበሬታታት ለጥፉ
*   ፋይላት ጽዓኑ (PDF, PowerPoint, Word)

ብዝሒ ሕቶታት፣ ምርጫታት መልሲን ክንደይ ቅኑዕ መልሲ ከም ዝፍጠርን ብምምራጽ ደረጃ ጸገም ባዕልኹም ትውስኑ።

ብተወሳኺ፣ እቲ ኣፕሊኬሽን ከም መንበቢ ናይ NDLA ትምህርቲ ጽሑፍ ኮይኑ የገልግል፣ ስለዚ ሕቶታት ቅድሚ ምድላውኩም ነቲ ትሕዝቶ ክትርእይዎን ክትግምግምዎን ትኽእሉ።

_ጽቡቕ ዕድል ኣብ ስራሕኩም!_

PS: ጌጋታት ረኺብኩም ወይ ርእይቶ ኣለኩም? በዚ ተወከሱ borchgrevink@gmail.com"""
    },
    "th": {
        "title": "เครื่องมือสร้างข้อสอบปรนัย",
        "language": "ภาษา",
        "login_google": "เข้าสู่ระบบด้วย Google",
        "welcome": "ยินดีต้อนรับ",
        "logout": "ออกจากระบบ",
        "navigation": "การนำทาง",
        "module_quiz": "เครื่องมือสร้างแบบทดสอบ",
        "module_ndla": "เนื้อหา NDLA",
        "settings": "การตั้งค่า",
        "source": "เลือกแหล่งที่มา:",
        "source_pdf": "ประวัติศาสตร์ข้ามพรมแดน (หนังสือเรียน)",
        "source_ndla": "NDLA (แหล่งข้อมูลออนไลน์)",
        "update_topics": "อัปเดตหัวข้อ",
        "topics_found": "พบ {} หัวข้อ",
        "select_topic": "เลือกหัวข้อ",
        "ndla_info": "เลือกหัวข้อและบทความจากฐานข้อมูล NDLA ด้านล่าง",
        "ndla_expand": "เลือกเนื้อหา NDLA",
        "selected_articles": "เลือก {} บทความ",
        "no_articles": "ไม่ได้เลือกบทความ",
        "num_questions": "จำนวนคำถาม",
        "num_options": "จำนวนตัวเลือก",
        "multiple_correct": "คำตอบที่ถูกต้องหลายข้อ (สูงสุด 2)",
        "generate_btn": "สร้างแบบทดสอบ",
        "analyzing_pdf": "กำลังวิเคราะห์ PDF...",
        "fetching_text": "กำลังดึงข้อความจาก {}...",
        "error_ndla_select": "คุณต้องเลือกบทความอย่างน้อยหนึ่งบทความจาก NDLA",
        "generating": "กำลังสร้างคำถามด้วย AI (OpenAI GPT-4o)...",
        "error_gen": "เกิดข้อผิดพลาดในการสร้าง: {}",
        "quiz_header": "แบบทดสอบ: {}",
        "submit_btn": "ส่งคำตอบ",
        "results_header": "ผลลัพธ์",
        "question": "คำถาม",
        "your_answer_correct": "✅ (คำตอบของคุณ - ถูกต้อง)",
        "your_answer_wrong": "❌ (คำตอบของคุณ - ผิด)",
        "correct_answer": "⚠️ (คำตอบที่ถูกต้อง)",
        "justification": "เหตุผล",
        "score": "คะแนนของคุณ",
        "result_cat": "ผลลัพธ์: {}",
        "download_pdf": "ดาวน์โหลดผลลัพธ์ (PDF)",
        "new_quiz": "ทำแบบทดสอบใหม่",
        "admin_panel": "แสดงแผงผู้ดูแลระบบ",
        "admin_header": "ผู้ดูแลระบบ: ผลลัพธ์ (จากฐานข้อมูล)",
        "admin_tools": "**เครื่องมือ:**\n- [เปิดมุมมองฐานข้อมูล NDLA](http://localhost:8000/ndla_content_viewer.html) (ต้องใช้เซิร์ฟเวอร์ภายในเครื่อง)",
        "select_user": "เลือกผู้ใช้เพื่อดูรายละเอียด",
        "results_for": "ผลลัพธ์สำหรับ: {}",
        "total_quizzes": "แบบทดสอบทั้งหมด",
        "total_questions": "คำถามทั้งหมด",
        "total_score": "คะแนนรวม",
        "avg_score": "คะแนนเฉลี่ย",
        "results_per_topic": "ผลลัพธ์ตามหัวข้อ",
        "history": "ประวัติ",
        "download_csv": "ดาวน์โหลดผลลัพธ์ทั้งหมด (CSV)",
        "no_results": "ยังไม่พบผลลัพธ์",
        "ndla_viewer_header": "เนื้อหา NDLA",
        "ndla_viewer_info": "ดึงเนื้อหาจากฐานข้อมูลภายในเครื่องตามการขูดข้อมูล NDLA",
        "ndla_viewer_error": "ไม่สามารถโหลดมุมมองเนื้อหา: {}",
        "reset_app": "รีเซ็ตแอป (แก้ไขจุดบกพร่อง)",
        "url_input_label": "URL ไปยังเว็บไซต์",
        "fetch_and_gen_btn": "ดึงเนื้อหาและสร้างแบบทดสอบ",
        "paste_url_warning": "คุณต้องวาง URL ก่อน",
        "fetch_content_spinner": "กำลังดึงเนื้อหาจากเว็บไซต์...",
        "no_text_found": "ไม่พบข้อความในหน้า",
        "paste_urls_info": "วาง URL ของบทความที่คุณต้องการสร้างคำถาม คุณสามารถเพิ่มหลาย URL ได้โดยกด Enter ระหว่างแต่ละ URL",
        "urls_input_label": "URL (หนึ่งรายการต่อบรรทัด):",
        "fetch_urls_btn": "ดึงเนื้อหาจาก {} URL",
        "welcome_message": """**ยินดีต้อนรับสู่เครื่องมือสร้างข้อสอบปรนัย!**

เครื่องมือนี้พัฒนาขึ้นเพื่อให้ง่ายและมีประสิทธิภาพในการสร้างข้อสอบปรนัยที่ดี คุณสามารถดึงเนื้อหาวิชาได้โดยตรงจากหนังสือเรียน *Historie på tvers* หรือจากแหล่งข้อมูลที่ครอบคลุมของ NDLA

คุณยังมีความยืดหยุ่นสูงในการใช้เนื้อหาของคุณเอง:
*   วางข้อความจากเว็บไซต์
*   อัปโหลดไฟล์ (PDF, PowerPoint, Word)

คุณควบคุมระดับความยากได้ด้วยตัวเองโดยเลือกจำนวนคำถาม ตัวเลือกคำตอบ และจำนวนคำตอบที่ถูกต้องที่จะสร้าง

นอกจากนี้ แอปยังทำหน้าที่เป็นผู้อ่านสำหรับเนื้อหาวิชา NDLA เพื่อให้คุณสามารถเรียกดูและประเมินเนื้อหาก่อนสร้างคำถาม

_ขอให้โชคดีกับการทำงาน!_

PS: พบข้อผิดพลาดหรือมีข้อเสนอแนะ? ติดต่อที่ borchgrevink@gmail.com"""
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
        "generating": "Генерація питань за допомогою ШІ (OpenAI GPT-4o)...",
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
        "reset_app": "Скинути додаток (Debug)",
        "url_input_label": "URL веб-сайту",
        "fetch_and_gen_btn": "Отримати контент та згенерувати тест",
        "paste_url_warning": "Спочатку потрібно вставити URL.",
        "fetch_content_spinner": "Отримання контенту з веб-сайту...",
        "no_text_found": "Текст на сторінці не знайдено.",
        "paste_urls_info": "Вставте URL-адреси статей, з яких ви хочете згенерувати питання. Ви можете додати кілька URL-адрес, натискаючи Enter між ними.",
        "urls_input_label": "URL-адреси (одна на рядок):",
        "fetch_urls_btn": "Отримати контент з {} URL-адрес",
        "welcome_message": """**Ласкаво просимо до Генератора тестів з варіантами відповідей!**

Цей інструмент розроблено для того, щоб зробити створення якісних тестів з варіантами відповідей простим та ефективним. Ви можете отримувати навчальний матеріал безпосередньо з підручника *Historie på tvers* або з обширних ресурсів NDLA.

Ви також маєте велику гнучкість у використанні власного матеріалу:
*   Вставляйте текст з веб-сайтів
*   Завантажуйте файли (PDF, PowerPoint, Word)

Ви самі керуєте рівнем складності, вибираючи кількість питань, варіантів відповідей та скільки правильних відповідей потрібно згенерувати.

Крім того, додаток працює як читач для навчального матеріалу NDLA, тому ви можете переглядати та оцінювати контент перед створенням питань.

_Успіхів у роботі!_

PS: Виявили помилки або маєте пропозиції? Зв'яжіться за адресою borchgrevink@gmail.com"""
    },
    "tig": {
        "title": "መውለዲ ብዙሕ ምርጫ",
        "language": "ሉገት",
        "login_google": "ብ Google እተው",
        "welcome": "መርሓባ",
        "logout": "ውጻእ",
        "navigation": "መዋፈሪ",
        "home": "ቤት",
        "my_history": "ታሪኸይ",
        "module_quiz": "መውለዲ ፈተና",
        "module_ndla": "ትሕዝቶ NDLA",
        "settings": "ቅንብራት",
        "source": "ምንጪ ምረጽ:",
        "source_pdf": "Historie på Tvers (መጽሓፍ)",
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
        "generating": "ብ AI ሕቶታት ይፈጥር ኣሎ (OpenAI GPT-4o)...",
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
        "ndla_viewer_info": "ትሕዝቶ ካብ ናይ ከባቢ ቋት ሓበሬታ ተወሲዱ (NDLA scraping)።",
        "ndla_viewer_error": "መራእይ ትሕዝቶ ክጽዕን ኣይተኻእለን: {}",
        "welcome_message": """**Merhaba! (Nab Mewledi Bizuh Mircha Enkwae Bdehan Metsakum!)**

Elli mesarhi tsubuq nay bizuh mircha hitotat biqelilu nimdilaw zitedalewe tu. Nay timhirti tsihuf kel *Historie på tvers* wey kel NDLA ketamtsu tikdu.

Nay geza risikum tsihuf nimtiqam gabi teatsatsafnet alekum:
*   Tsihuf kel merbeb habereta letifu
*   Files tsaanu (PDF, PowerPoint, Word)

Bizhi hitotat, mircha melsi, wa kindey qinu melsi kem zifeter bimimrats dereja tsegem baalkum tiwesnu.

Bite we saki, elli app kem menbebi nay NDLA timhirti tsihuf koynu yegelgil, slezi hitotat qidmi mimdilawkum neti tihizto kitriwo tikdu.

_Tsubuq idil ab sirahkum!_

PS: Gegatat rekibkum wey reyito alekum? Bezi tewekesu borchgrevink@gmail.com""",
        "reset_app": "ኣፕሊኬሽን ዳግማይ ጀምር (Debug)",
        "url_input_label": "URL ናብ መርበብ ሓበሬታ",
        "fetch_and_gen_btn": "ትሕዝቶ ኣምጽእ እሞ ፈተና ፍጠር",
        "paste_url_warning": "ቅድም URL ክትለጥፍ ኣለካ።",
        "fetch_content_spinner": "ትሕዝቶ ካብ መርበብ ሓበሬታ የውጽእ ኣሎ...",
        "no_text_found": "ኣብቲ ገጽ ዝኾነ ጽሑፍ ኣይተረኽበን።",
        "paste_urls_info": "URL ናይቶም ሕቶታት ክትፈጥረሎም እትደሊ ዓንቀጻት ለጥፍ። ኣብ መንጎ ነፍሲ ወከፍ Enter ብምርጋጽ ብዙሓት URL ክትውስኽ ትኽእል ኢኻ።",
        "urls_input_label": "URLs (ሓደ ኣብ ነፍሲ ወከፍ መስመር):",
        "fetch_urls_btn": "ትሕዝቶ ካብ {} URLs ኣምጽእ"
    },
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
        }}
        
        /* Add "MENY" text */
        [data-testid="stSidebarCollapsedControl"]::after {{
            content: "MENY";
            font-weight: 900;
            font-size: 18px; /* Larger font */
            letter-spacing: 1.5px;
            text-transform: uppercase;
        }}
        
        [data-testid="stSidebarCollapsedControl"] svg {{
            height: 28px !important; /* Larger icon */
            width: 28px !important;
            fill: white !important;
        }}
        
        /* Make the header toolbar background visible on mobile to contrast the button */
        header[data-testid="stHeader"] {{
            background-color: #0e1117;
            z-index: 99999;
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


def render_admin_panel():
    # --- Clear Cache Button ---
    if st.button("🗑️ Tøm mellomlager (Cache)", help="Trykk her hvis du ikke ser endringer i innholdet."):
        st.cache_data.clear()
        st.success("Mellomlager tømt! Appen lastes på nytt...")
        import time
        time.sleep(1)
        st.rerun()

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
    st.info("📊 **Resultater**")
    
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
            # Download button (always available when loaded)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                get_text("download_csv"),
                csv,
                "quiz_results.csv",
                "text/csv",
                key='download-csv'
            )
            
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
                    if c1.checkbox("", key=f"del_{row['id']}"):
                        delete_ids.append(row['id'])
                    c2.write(row['timestamp'])
                    c3.write(row['topic'])
                    c4.write(row['score'])
                    c5.write(f"{row['percentage']:.1f}%")
                    
                if delete_ids:
                    if st.button(f"Slett {len(delete_ids)} valgte resultater", type="primary"):
                        if delete_results(result_ids=delete_ids):
                            st.success("Slettet valgte resultater.")
                            st.rerun()
            else:
                st.dataframe(df)
        else:
            st.info("Ingen resultater funnet ennå.")
    
    st.divider()

    # --- 3. Login Logs Section ---
    with st.expander("📋 **Innlogginger**", expanded=False):
        from storage import get_login_logs
        logs_df = get_login_logs()
        
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("Ingen innlogginger registrert ennå.")

    st.divider()

    # --- 4. User Permissions Management ---
    with st.expander("🔒 **Rettighetsstyring**", expanded=False):
        from storage import get_all_permissions, grant_permission
        
        # List all users with permissions
        perms_df = get_all_permissions()
        
        # We also want to see users who have logged in but might not be in the permissions table yet
        # So let's merge with login logs or just list unique emails from logs
        all_users = set()
        if not logs_df.empty:
            all_users.update(logs_df['user_email'].unique())
        if not perms_df.empty:
            all_users.update(perms_df['user_email'].unique())
            
        # Create a DataFrame for display/editing
        user_list = []
        for email in all_users:
            # Get current permission
            can_download = False
            if not perms_df.empty and email in perms_df['user_email'].values:
                can_download = bool(perms_df[perms_df['user_email'] == email]['can_download'].iloc[0])
            
            # Admins always have access
            is_admin = email in ADMINS
            if is_admin:
                can_download = True
                
            user_list.append({"user_email": email, "can_download": can_download, "is_admin": is_admin})
            
        users_df = pd.DataFrame(user_list)
        
        if not users_df.empty:
            # Display as a data editor? Or just a list with checkboxes?
            # Data editor is cleaner
            
            st.write("Administrer nedlastningstilgang (MS Forms / PDF):")
            
            # We need to handle updates. 
            # Let's iterate and show toggles.
            
            for index, row in users_df.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(row['user_email'])
                
                if row['is_admin']:
                    c2.success("Admin")
                else:
                    # Checkbox for permission
                    new_perm = c2.checkbox("Tilgang", value=row['can_download'], key=f"perm_{row['user_email']}")
                    if new_perm != row['can_download']:
                        if grant_permission(row['user_email'], new_perm):
                            st.toast(f"Oppdaterte rettigheter for {row['user_email']}")
                            # We might need to rerun to refresh the list source of truth, but toast is nice
                            
        else:
            st.info("Ingen brukere funnet.")

    st.divider()

    # (Energy Monitoring moved to separate app)

    st.divider()

    # --- 3. Content Update Section (Moved to Bottom) ---
    st.info("🛠️ **Verktøy for innholdsoppdatering**")
    
    st.write("Her kan du hente siste versjon av innholdet fra NDLA. Velg fag og emner du vil oppdatere.")
    
    # Fetch available topics for this subject
    from scrape_ndla import get_subject_topics, update_topic, SUBJECTS
    
    # Select Subject
    update_subject = st.selectbox(
        "Velg fag å oppdatere:",
        list(SUBJECTS.keys()),
        key="update_subject"
    )
    
    @st.cache_data(ttl=3600)
    def get_cached_subject_topics(subject):
        return get_subject_topics(subject)
    
    with st.spinner(f"Henter emner for {update_subject}..."):
        available_topics = get_cached_subject_topics(update_subject)
        
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
    
    # --- Debug Button ---
    st.divider()
    if st.button("Nullstill app (Debug)", type="primary"):
        for key in list(st.session_state.keys()):
            # Keep language settings
            if key not in ["language", "lang_selector", "lang_selector_login"]:
                del st.session_state[key]
        
        # Also clear cookies if possible
        try:
            from streamlit_app import cookie_manager # Ensure access
            cookie_manager.delete("user_email")
        except:
            pass
        st.rerun()

def render_quiz_generator(cookie_manager):

    # --- App Logic ---
    
    # Sidebar
    st.sidebar.header(get_text("settings"))
    
    # Source Selection
    source_type = st.sidebar.radio(
        get_text("choose_source"),
        [get_text("source_pdf"), get_text("source_ndla"), "Nettside (URL)", "Filopplasting (PDF/Word/PPT)"],
        label_visibility="collapsed"
    )
    
    selected_text = ""
    selected_topic_name = ""
    
    # Trigger variable
    trigger_generation = False
    final_text = ""
    final_topic_name = ""
    
    if source_type == "Nettside (URL)":
        st.sidebar.info(get_text("paste_urls_info"))
        url_input = st.sidebar.text_input(get_text("url_input_label"), key="url_input")
        
        # Combined button - always visible
        if st.sidebar.button(get_text("fetch_and_gen_btn"), type="primary"):
            if not url_input:
                st.sidebar.warning(get_text("paste_url_warning"))
            else:
                with st.spinner(get_text("fetch_content_spinner")):
                    try:
                        from scrape_url import scrape_url
                        text = scrape_url(url_input)
                        if text:
                            # Set session state for persistence (optional, but good for history)
                            st.session_state['url_text'] = text
                            st.session_state['url_source'] = url_input
                            
                            # Trigger generation immediately
                            trigger_generation = True
                            final_text = text
                            final_topic_name = "Nettside: " + url_input
                            
                        else:
                            st.sidebar.warning(get_text("no_text_found"))
                    except Exception as e:
                        st.sidebar.error(f"Feil: {e}")
    
                        st.sidebar.error(f"Feil: {e}")
        st.sidebar.info(get_text("paste_urls_info"))
        
        # Use text_area for multiple URLs
        urls_input = st.sidebar.text_area(get_text("urls_input_label"), height=150, placeholder="https://example.com/artikkel1\nhttps://example.com/artikkel2", key="urls_input")
        
        if urls_input:
            urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
            
            if urls:
                if st.sidebar.button(get_text("fetch_urls_btn").format(len(urls)), key="fetch_urls_btn"):
                    with st.spinner("Henter innhold..."):
                        combined_text = ""
                        valid_urls = 0
                        
                        for url in urls:
                            try:
                                import requests
                                from bs4 import BeautifulSoup
                                
                                response = requests.get(url)
                                if response.status_code == 200:
                                    soup = BeautifulSoup(response.text, 'html.parser')
                                    # Try to find main content
                                    # This is a heuristic
                                    content_div = soup.find('article') or soup.find('main') or soup.body
                                    if content_div:
                                        text = content_div.get_text(separator='\n', strip=True)
                                        combined_text += f"\n\n--- Kilde: {url} ---\n\n{text}"
                                        valid_urls += 1
                            except Exception as e:
                                st.sidebar.error(f"Kunne ikke hente {url}: {e}")
                        
                        if valid_urls > 0:
                            st.session_state['quiz_source_text'] = combined_text
                            st.session_state['quiz_source_name'] = f"Nettsider ({valid_urls} kilder)"
                            st.sidebar.success(f"Hentet innhold fra {valid_urls} URL-er!")
                        else:
                            st.sidebar.error("Fant ikke noe innhold på URL-ene.")
            else:
                st.sidebar.warning("Vennligst lim inn minst én URL.")
        
        # If content has been fetched, allow generation
        if 'quiz_source_text' in st.session_state and st.session_state['quiz_source_text']:
            if st.sidebar.button("Generer quiz fra hentet innhold", type="primary", key="generate_from_urls_btn"):
                final_text = st.session_state['quiz_source_text']
                final_topic_name = st.session_state.get('quiz_source_name', "Nettsider")
                trigger_generation = True
        else:
            st.sidebar.info("Lim inn URL-er og trykk 'Hent innhold' for å fortsette.")

    elif source_type == "Filopplasting (PDF/Word/PPT)":
        st.sidebar.info("Last opp en fil (PDF, DOCX, PPTX) for å lage quiz.")
        uploaded_file = st.sidebar.file_uploader("Velg fil", type=["pdf", "docx", "pptx"])
        
        if uploaded_file:
            if st.sidebar.button("Generer quiz fra fil", type="primary"):
                with st.spinner("Leser fil..."):
                    try:
                        from file_processor import extract_text_from_file
                        text = extract_text_from_file(uploaded_file)
                        if text:
                            trigger_generation = True
                            final_text = text
                            final_topic_name = f"Fil: {uploaded_file.name}"
                        else:
                            st.sidebar.warning("Fant ingen tekst i filen.")
                    except Exception as e:
                        st.sidebar.error(f"Feil ved lesing av fil: {e}")

    elif source_type == get_text("source_pdf"):
        # Topics
        # Topics
        if "topics" not in st.session_state or st.sidebar.button(get_text("update_topics")):
            with st.spinner(get_text("analyzing_pdf")):
                all_topics = {}
                for pdf_file in PDF_FILES:
                    # Check if file exists
                    import os
                    if os.path.exists(pdf_file):
                        file_topics = get_topics(pdf_file)
                        # Prefix topics with filename or just merge?
                        # User wants "equal footing", but we need to avoid collisions.
                        # Let's append (File) if collision, or just rely on unique names.
                        # Actually, let's store the source file in the value.
                        for topic, (start, end) in file_topics.items():
                            # Debug collision
                            if topic in all_topics:
                                print(f"DEBUG: Collision for '{topic}'. Existing: {all_topics[topic][2]}, New: {pdf_file}")
                                # Prefer HPT.pdf for Tema 1-5? 
                                # If HPT.pdf is first, and we want to keep it, we should NOT overwrite.
                                # But let's just log for now to confirm.
                            
                            # Simple merge for now, but let's prevent HPTx from overwriting HPT if HPT is the main source
                            if topic in all_topics and "HPT.pdf" in all_topics[topic][2] and "HPTx.pdf" in pdf_file:
                                print(f"DEBUG: Ignoring {topic} from {pdf_file} because it exists in {all_topics[topic][2]}")
                                continue
                            
                            # Manual Override for Tema 1 (User reported 9-17)
                            # "Tema 1" might be "Tema 1: Introkapittel"
                            if "Tema 1" in topic and "HPT.pdf" in pdf_file:
                                print(f"DEBUG: Overriding {topic} range to 8-17 (Pages 9-17)")
                                start = 8  # Page 9
                                end = 17   # Page 17 (inclusive) -> index 17 (exclusive)
                                
                            all_topics[topic] = (start, end, pdf_file)
                    else:
                        st.sidebar.warning(f"Fant ikke filen: {pdf_file}")
                
                print(f"DEBUG: Final topics: {list(all_topics.keys())}")
                st.session_state.topics = all_topics
                
        topic_names = list(st.session_state.topics.keys())
        
        # Using a key ensures the selection persists even if other things update
        selected_topic = st.sidebar.selectbox(get_text("select_topic"), topic_names, key="topic_selector")
        selected_topic_name = selected_topic
        
        if st.sidebar.button(get_text("generate_btn")):
             start_page, end_page, source_pdf = st.session_state.topics[selected_topic]
             with st.spinner(get_text("fetching_text", selected_topic)):
                 final_text = extract_text_by_topic(source_pdf, start_page, end_page)
                 final_topic_name = selected_topic_name
                 trigger_generation = True

    else: # NDLA
        st.sidebar.info(get_text("ndla_info"))
        hierarchy = get_content_hierarchy()
        
        st.subheader(get_text("navigation"))
        selected_articles = render_ndla_selector(hierarchy)
        
        if selected_articles:
            st.success(get_text("selected_articles", len(selected_articles)))
            # Combine text
            selected_text = "\n\n".join([art['content'] for art in selected_articles])
            
            # Display content in a nice container
            st.markdown(f"""
            <div style="background-color: #262730; padding: 30px; border-radius: 10px; border: 1px solid #444;">
                {selected_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Topic name? Maybe "NDLA Utvalg" or list topics?
            if len(selected_articles) == 1:
                selected_topic_name = selected_articles[0]['title']
            else:
                selected_topic_name = f"NDLA Utvalg ({len(selected_articles)} artikler)"
                
            if st.sidebar.button(get_text("generate_btn")):
                final_text = selected_text
                final_topic_name = selected_topic_name
                trigger_generation = True
        else:
            st.info(get_text("ndla_info"))
    
    # Get configured max limit
    from storage import get_setting
    
    max_q_limit = int(get_setting("max_question_limit", 20))
    
    num_questions = st.sidebar.slider(get_text("num_questions"), 1, max_q_limit, min(5, max_q_limit))
    num_options = st.sidebar.slider(get_text("num_options"), 2, 6, 4)
    multiple_correct = st.sidebar.checkbox(get_text("multiple_correct"), value=False)
    
    # Common Generation Logic
    if trigger_generation:
        if not final_text:
             st.error("Ingen tekst å generere fra.")
        else:
            with st.spinner(get_text("generating")):
                # Pass language to generate_quiz
                lang = st.session_state.get("language", "no")
                quiz_data = generate_quiz(final_text, num_questions, num_options, multiple_correct, language=lang)
                
                if "error" in quiz_data:
                    st.error(get_text("error_gen", quiz_data['error']))
                else:
                    st.session_state.quiz_data = quiz_data
                    st.session_state.current_answers = {}
                    st.session_state.quiz_submitted = False
                    st.session_state.selected_topic_name = final_topic_name # Store for results
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

    # Tabs
    # Display Results
    if st.session_state.get("quiz_submitted", False):
        st.header(get_text("results_header"))
        
        questions = st.session_state.quiz_data.get("questions", [])
        answers = st.session_state.current_answers
        
        score = 0
        total_possible = 0
        
        for i, q in enumerate(questions):
            # Robustly get correct indices
            correct_indices = q.get('correct_indices')
            if correct_indices is None:
                # Fallback: Check for 'correct_index' (single) or 'answer'
                if 'correct_index' in q:
                    correct_indices = [q['correct_index']]
                elif 'answer' in q: # Sometimes returns string answer
                     # Try to find index of answer string in options
                     try:
                         idx = q['options'].index(q['answer'])
                         correct_indices = [idx]
                     except:
                         correct_indices = []
                else:
                    correct_indices = []
            
            # Ensure correct_indices is added to the question object for PDF generation
            q['correct_indices'] = correct_indices
            
            user_indices = answers.get(i, [])
            
            q_score = 0
            q_max = len(correct_indices)
            
            # Let's calculate points
            for idx in user_indices:
                # Ensure we are comparing integers
                if int(idx) in [int(ci) for ci in correct_indices]:
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
        
        # --- Permissions Check for Downloads ---
        from storage import get_user_permissions, grant_permission
        
        # Check permissions
        can_download = get_user_permissions(st.session_state.user_email)
        
        # Admins always have permission
        if st.session_state.user_email in ADMINS:
            can_download = True
            # Ensure admin is in the DB with permission
            grant_permission(st.session_state.user_email, True)

        if can_download:
            # Word Download (MS Forms)
            docx_file = generate_docx(questions)
            st.download_button(
                label="Last ned for MS Forms (Word)",
                data=docx_file,
                file_name="quiz_ms_forms.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.info("Du har ikke tilgang til å laste ned resultatene. Kontakt administrator for tilgang.")
            if st.button("Be om tilgang"):
                # Ideally we would log this request, for now just show a message
                st.success("Forespørsel sendt (simulert). Kontakt admin direkte.")
        
        if st.button(get_text("new_quiz")):
            del st.session_state.quiz_data
            del st.session_state.quiz_submitted
            if "result_saved" in st.session_state:
                del st.session_state.result_saved
            st.rerun()

def main():
    # --- Cookie Manager Strategy (v1.8.28) ---
    # We MUST delay cookie_manager init if we are performing an auth code exchange.
    # Initializing it triggers a reload, which kills the auth request -> "Expired Code".
    
    cookie_manager = None
    
    # Check if we have an auth code to process
    has_auth_code = "code" in st.query_params
    
    if has_auth_code and "user_email" not in st.session_state:
        st.session_state["auth_status"] = "Auth Code Detected - Delaying Cookie Manager..."
        # Do NOT init cookie_manager yet!
    else:
        # Safe to init
        cookie_manager = stx.CookieManager(key="cm_main")

    # Initialize Language FIRST
    if "language" not in st.session_state:
        st.session_state.language = "no"

    # --- CSS for Mobile/Sidebar ---
    st.markdown("""
        <style>
            [data-testid="stSidebarCollapseButton"] {
                font-size: 3rem !important;
                color: #4285F4 !important;
                display: flex !important;
                flex-direction: row !important; /* CHANGED TO ROW */
                align-items: center !important;
                justify-content: center !important;
                gap: 8px !important;
                width: auto !important;
                height: auto !important;
                padding: 5px !important;
                visibility: visible !important;
                display: block !important;
                z-index: 9999999 !important; /* Extremely high z-index */
                background-color: transparent !important;
                border: none !important;
                
                /* FORCE FIXED POSITION ALWAYS */
                position: fixed !important;
                top: 15px !important;
                left: 10px !important;
                box-shadow: none !important;
                
                /* Ensure text color is visible against white background */
                color: #4285F4 !important;
                
                /* Ensure container allows overflow for text */
                overflow: visible !important;
                display: flex !important;
            }
            
            /* RESTORE children (SVG) visibility */
            [data-testid="stSidebarCollapseButton"] > * {
                display: flex !important; /* or block, depending on what it was */
            }
            
            /* Default Text: "Åpne meny" - APPLIED TO CONTAINER */
```
            /* Dynamic Text: "Lukk meny" removed as per user request */
            
            [data-testid="stSidebarCollapseButton"]:hover {
                transform: scale(1.05) !important;
                transition: transform 0.2s;
                cursor: pointer;
            }


        </style>
    """, unsafe_allow_html=True)




    # --- Authentication Logic (Must run before widgets) ---
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
    
    # Initialize Cookie Manager
    # cookie_manager = stx.CookieManager() # Now global

    # Check if we are already logged in
    if "token" not in st.session_state:
        # Check if we have a code from the redirect
        query_params = st.query_params
        code = query_params.get("code")
        state = query_params.get("state")
        
        # Handle list if necessary
        if isinstance(state, list):
            state = state[0]
        
        if code:
            st.session_state["pre_check_trace"] = f"Code: {code}, Last: {st.session_state.get('last_auth_code')}"
            
            # Check if we already tried this code
            if code == st.session_state.get("last_auth_code"):
                # Do NOT overwrite auth_status, so we can see what happened in the first run
                reuse_msg = f"Gjenbruk oppdaget. Forrige status: {st.session_state.get('auth_status')}"
                st.session_state["reuse_trace"] = reuse_msg
                
                st.error(reuse_msg) # Show the error!
                st.warning("Vi prøver likevel... (Debugging)")
                
                # if st.button("🔄 Nullstill app (hvis du står fast)"):
                #     st.session_state.clear()
                #     st.query_params.clear()
                #     st.rerun()
                    
                # st.query_params.clear()
                # return # STOP THE EXECUTION HERE - DISABLED FOR DEBUGGING
            
            st.session_state["auth_status"] = "New code. Starting exchange..."
            st.session_state.last_auth_code = code # Set IMMEDIATELY to catch reloads
            
            # Parse state to get provider and language
            # Format: "provider|language" (e.g., "google|no" or "microsoft|en")
            provider = "google" # Default
            language = "no"
            
            if state:
                parts = state.split('|')
                if len(parts) >= 2:
                    provider = parts[0]
                    language = parts[1]
                elif state in ["no", "en", "ar", "so", "ti", "uk", "th"]:
                    # Legacy state (just language)
                    language = state
            
            # Restore language
            if language in ["no", "en", "ar", "so", "ti", "uk", "th"]:
                st.session_state.language = language
                st.session_state["lang_selector"] = language
                if "lang_selector_login" in st.session_state:
                    st.session_state["lang_selector_login"] = language
                
            try:

                import jwt # PyJWT
                
                token_data = None
                user_email = None
                user_name = None
                
                if provider == "google":
                    token_url = "https://oauth2.googleapis.com/token"
                    data = {
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code"
                    }
                    response = requests.post(token_url, data=data)
                    token_data = response.json()
                    
                    if "id_token" in token_data:
                        # Decode Google ID Token
                        # We use the same logic as before (simple decode)
                        import base64
                        import json
                        id_token = token_data["id_token"]
                        parts = id_token.split('.')
                        if len(parts) > 1:
                            payload_b64 = parts[1]
                            payload_b64 += '=' * (-len(payload_b64) % 4)
                            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                            user_email = payload.get("email")
                            user_name = payload.get("name", "Unknown")
                    elif "error" in token_data:
                        st.error(f"Google Error: {token_data}")

                elif provider == "microsoft":
                    if "microsoft" not in st.secrets:
                        st.error("Microsoft secrets missing!")
                        st.stop()
                        
                    ms_client_id = st.secrets["microsoft"]["client_id"]
                    ms_tenant_id = st.secrets["microsoft"]["tenant_id"]
                    ms_client_secret = st.secrets["microsoft"]["client_secret"]
                    ms_redirect_uri = st.secrets["microsoft"]["redirect_uri"]
                    
                    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
                    data = {
                        "client_id": ms_client_id,
                        "scope": "User.Read openid profile email",
                        "code": code,
                        "redirect_uri": ms_redirect_uri,
                        "grant_type": "authorization_code",
                        "client_secret": ms_client_secret,
                    }
                    
                    if not ms_client_secret:
                        st.error("Mangler client_secret i secrets.toml!")
                        return

                    st.session_state["auth_status"] = "Posting to token endpoint (requests)..."
                    try:
                        response = requests.post(token_url, data=data, timeout=10)
                        st.session_state["auth_status"] = f"Token response: {response.status_code}"
                        
                        if response.status_code == 200:
                            token_data = response.json()
                        else:
                            st.session_state["auth_status"] = f"HTTP Error {response.status_code}: {response.reason}"
                            st.session_state["auth_error"] = f"Details: {response.text}"
                            
                            # Check for AADSTS70000 (Expired Code) - Race Condition Handler
                            if "AADSTS70000" in response.text:
                                st.warning("Koden er utløpt (AADSTS70000). Sjekker om vi allerede er logget inn...")
                                import time
                                time.sleep(1) 
                                
                                # NOW we can try to init cookie manager to check
                                if not cookie_manager:
                                    cookie_manager = stx.CookieManager(key="cm_rescue")
                                    import time
                                    time.sleep(1) # Wait for load
                                
                                # Check cookies directly
                                saved_email = cookie_manager.get("user_email")
                                if saved_email:
                                    st.success(f"Fant lagret sesjon for {saved_email}! Fortsetter...")
                                    st.session_state.user_email = saved_email
                                    st.session_state.user_name = cookie_manager.get("user_name", "Unknown")
                                    st.query_params.clear()
                                    st.rerun()
                                    return
                                else:
                                    st.error("Koden var utløpt og ingen sesjon ble funnet. Prøv igjen.")
                            else:
                                st.error(f"Autentiseringsfeil: {response.reason}")
                                st.warning("Her er detaljene fra Microsoft:")
                                st.code(response.text, language="json")

                            st.query_params.clear()
                            return

                    except Exception as req_err:
                        st.session_state["auth_status"] = f"Request failed: {req_err}"
                        st.session_state["auth_error"] = f"Exception: {str(req_err)}"
                        st.error(f"Feil under token-utveksling: {req_err}")
                        return # Stop, do not raise
                        
                    st.session_state["auth_status"] = "Token received. Checking access..."

                    st.session_state["auth_status"] = "Token received. Checking access..."
                    
                    if "access_token" in token_data:
                        st.session_state["auth_status"] = "Access token found. Fetching Graph..."
                        # Get user info from Graph API
                        access_token = token_data["access_token"]
                        
                        # Use requests instead of urllib
                        headers = {"Authorization": f"Bearer {access_token}"}
                        
                        try:
                            graph_response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers, timeout=10)
                            
                            if graph_response.status_code == 200:
                                user_info = graph_response.json()
                                user_email = user_info.get("mail") or user_info.get("userPrincipalName")
                                user_name = user_info.get("displayName", "Unknown")
                                st.session_state["auth_status"] = "Graph success. Email found."
                            else:
                                st.error(f"Failed to fetch Microsoft user info: {graph_response.status_code}")
                                st.session_state["auth_status"] = f"Graph fail: {graph_response.status_code}"
                        except Exception as graph_err:
                             st.session_state["auth_status"] = f"Graph request failed: {graph_err}"
                             st.error(f"Feil mot Graph API: {graph_err}")
                             return # Stop, do not raise

                # Common Success Handling
                if token_data and ("access_token" in token_data or "id_token" in token_data) and user_email:
                    st.session_state.token = token_data
                    st.session_state.user_email = user_email
                    st.session_state.user_name = user_name
                    
                    st.session_state.user_name = user_name
                    
                    # Log login (exclude admin)
                    if user_email != "borchgrevink@gmail.com":
                        from storage import log_login
                        log_login(user_email, user_name)
                    
                    # Set persistent cookie
                    # NOW we init cookie manager if not already done
                    if not cookie_manager:
                        cookie_manager = stx.CookieManager(key="cm_success")
                        # This might trigger a reload, which is fine NOW because we have the token in session_state!
                    
                    import datetime
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("user_email", user_email, expires_at=expires, key="set_email")
                    cookie_manager.set("user_name", user_name, expires_at=expires, key="set_name")
                    
                    # st.session_state["login_trace"] = "Success block reached. Rerunning..."
                    
                    import time
                    time.sleep(0.5)
                    # Clear params to prevent "Reuse detected" on rerun
                    st.query_params.clear()
                    st.rerun()
                else:
                    error_desc = token_data.get('error_description', str(token_data))
                    if "AADSTS70000" in error_desc:
                        st.warning("Koblingen utløp. Vennligst klikk på knappen igjen.")
                    else:
                        st.error(f"Feil ved innlogging ({provider}): {error_desc}")
                    
                    st.query_params.clear() # Clear params to prevent loop
                    
            except Exception as e:
                st.error(f"Feil under token-utveksling: {e}")
                st.session_state["auth_error"] = f"Exception: {str(e)}"
                st.query_params.clear() # Clear params to prevent loop

            
    # --- Language Selector (Top of Sidebar) ---
    # lang_options moved below
    
    def update_lang():
        st.session_state.language = st.session_state.lang_selector

    # Version number moved to bottom of sidebar

    
    # Privacy Policy Link (Required for Google Verification)
    st.sidebar.markdown("---")
    st.sidebar.markdown("[📄 Personvernerklæring (Privacy Policy)](https://github.com/voxcuriosa/Flervalgsgenerator/blob/main/privacy_policy.md)")
    
    # Debug Info moved to top of main()
    

    lang_options = {
        "no": "🇳🇴 Norsk (Bokmål)", 
        "nn": "🇳🇴 Norsk (Nynorsk)",
        "en": "🇬🇧 English", 
        "ar": "🇸🇦 العربية", 
        "so": "🇸🇴 Soomaali", 
        "ti": "🇪🇷 ትግርኛ", 
        "uk": "🇺🇦 Українська",
        "th": "🇹🇭 ไทย",
        "tig": "🇪🇷 ትግረ"
    }

    lang_keys = list(lang_options.keys())
    try:
        current_index = lang_keys.index(st.session_state.language)
    except ValueError:
        current_index = 0

    st.sidebar.selectbox(
        get_text("language"),
        options=lang_keys,
        format_func=lambda x: lang_options[x],
        index=current_index,
        key="lang_selector",
        label_visibility="collapsed",
        on_change=update_lang
    )
    
    # --- Admin Button (Visible everywhere if admin) ---
    if st.session_state.get("user_email") and st.session_state.user_email in ADMINS:
        is_admin_open = st.session_state.get("show_admin", False)
        # Dynamic label
        btn_label = "🔙 Tilbake til meny" if is_admin_open else get_text("admin_panel")
        
        if st.sidebar.button(btn_label, key="admin_btn_top"):
            st.session_state.show_admin = not is_admin_open
            st.rerun()
            
    if st.session_state.get("show_admin", False) and st.session_state.get("user_email") and st.session_state.user_email in ADMINS:
        render_admin_panel()
        return # Stop rendering the rest of the app
            
    if st.session_state.get("user_email"):
        # --- Force Sidebar Open on Mobile (Aggressive JS Hack) - ONLY AFTER LOGIN ---
        # Streamlit defaults to collapsed on mobile. We want it open.
        
        components.html("""
            <script>
                (function() {
                    var attempts = 0;
                    var maxAttempts = 20; // Try for 2 seconds
                    var interval = setInterval(function() {
                        attempts++;
                        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
                        const button = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"]');
                        
                        if (sidebar && button) {
                            // Check if collapsed (aria-expanded is 'false')
                            if (sidebar.getAttribute('aria-expanded') === 'false') {
                                button.click();
                                console.log("Sidebar forced open by script (Post-Login)");
                            }
                            // We don't clear interval immediately to ensure it stays open if there's a race
                            if (attempts > 5) clearInterval(interval);
                        }
                        
                        if (attempts >= maxAttempts) {
                            clearInterval(interval);
                        }
                    }, 100);
                })();
            </script>
        """, height=0, width=0)
        


        # Clean URL if we have leftover auth params
        if "code" in st.query_params:
            st.query_params.clear()
            
        # Logout Button in Sidebar
        # Logout Button (Hard Logout Logic)
        if st.sidebar.button(get_text("logout")):
            # Clear cookies first
            try:
                cookie_manager.delete("user_email", key="del_email_hard")
                cookie_manager.delete("user_name", key="del_name_hard")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
            except:
                pass
            
            # JS Reload
            st.markdown("<meta http-equiv='refresh' content='0;URL=/' />", unsafe_allow_html=True)

    else:
            # Show Login Button
            # We show this INSTEAD of the main app if not logged in
            
            # Prevent flicker if we are in the middle of auth flow
            if "code" in st.query_params:
                 st.info("Logg inn pågår... Vennligst vent.")
                 return
            
            # Show Language Selector on Login Screen too!
            # st.sidebar.caption("v1.7.4") # REMOVED DUPLICATE
            st.image(LOGO_URL, width=150)
            st.title(get_text("title"))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Nullstill app", key="reset_login_page"):
                    st.session_state.clear()
                    st.query_params.clear()
                    st.rerun()
            with col2:
                # Network test removed
                pass
            

            
            lang_options = {
                "no": "🇳🇴 Norsk (Bokmål)", 
                "nn": "🇳🇴 Norsk (Nynorsk)",
                "en": "🇬🇧 English", 
                "ar": "🇸🇦 العربية", 
                "so": "🇸🇴 Soomaali", 
                "ti": "🇪🇷 ትግርኛ", 
                "uk": "🇺🇦 Українська",
                "th": "🇹🇭 ไทย",
                "tig": "🇪🇷 ትግረ"
            }
            selected_lang = st.radio(
                "Language / Språk / لغة", 
                options=list(lang_options.keys()), 
                format_func=lambda x: lang_options[x],
                index=0 if st.session_state.language == "no" else (1 if st.session_state.language == "nn" else (2 if st.session_state.language == "en" else (3 if st.session_state.language == "ar" else (4 if st.session_state.language == "so" else (5 if st.session_state.language == "ti" else (6 if st.session_state.language == "uk" else (7 if st.session_state.language == "th" else 8))))))),
                key="lang_selector_login",
                horizontal=True
            )
            
            if selected_lang != st.session_state.language:
                st.session_state.language = selected_lang
                st.rerun()
            
            if st.session_state.get("auth_status") == "Graph success. Email found.":
                 # Already logged in via Microsoft, skip Google check
                 pass
            else:
                # Check Google Auth
                # --- Google Auth URL ---
                scope = "openid email profile"
                params = {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": scope,
                    "access_type": "offline",
                    "prompt": "consent",
                    "state": st.session_state.language # Revert to just language for Google
                }
                # Use quote_via=urllib.parse.quote to get %20 instead of + for spaces
                import urllib.parse
                auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
                
                # --- Microsoft Auth URL ---
                ms_auth_url = None
                if "microsoft" in st.secrets:
                    ms_client_id = st.secrets["microsoft"]["client_id"]
                    ms_tenant_id = st.secrets["microsoft"]["tenant_id"]
                    ms_redirect_uri = st.secrets["microsoft"]["redirect_uri"]
                    
                    ms_params = {
                        "client_id": ms_client_id,
                        "response_type": "code",
                        "redirect_uri": ms_redirect_uri,
                        "response_mode": "query",
                        "scope": "User.Read openid profile email",
                        "state": f"microsoft|{st.session_state.language}",
                        "prompt": "select_account"
                    }
                    import urllib.parse
                    ms_auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urllib.parse.urlencode(ms_params)}"

                # --- Render Buttons ---
                # --- Google Auth ---
                import textwrap
                
                # Helper to clean HTML
                def clean_html(html):
                    return textwrap.dedent(html).strip()

                # Google Button
                google_btn = clean_html(f'''
                    <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color: #4285F4; 
                            color: white; 
                            padding: 12px 24px; 
                            border: none; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            font-size: 16px;
                            font-family: Roboto, sans-serif;
                            display: flex;
                            align-items: center;
                            gap: 12px;
                            width: 250px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        ">
                            <img src="https://www.google.com/favicon.ico" width="20" style="background: white; border-radius: 50%; padding: 2px;">
                            <span>{get_text("login_google")}</span>
                        </button>
                    </a>
                ''')

                # Microsoft Button
                if ms_auth_url:
                    ms_btn = clean_html(f'''
                        <a href="{ms_auth_url}" target="_blank" style="text-decoration: none;">
                            <button style="
                                background-color: #2F2F2F; 
                                color: white; 
                                padding: 12px 24px; 
                                border: 1px solid #555; 
                                border-radius: 4px; 
                                cursor: pointer; 
                                font-size: 16px;
                                font-family: Segoe UI, sans-serif;
                                display: flex;
                                align-items: center;
                                gap: 12px;
                                width: 250px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                            ">
                                <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg" width="20">
                                <span>Logg inn med Microsoft</span>
                            </button>
                        </a>
                        <p style="font-size: 12px; color: #888; margin-top: 5px; text-align: center;">(Kun personlig Microsoft-konto, ikke jobb/skole)</p>
                    ''')
                else:
                    # Disabled state
                    ms_btn = clean_html(f'''
                        <button style="
                            background-color: #2F2F2F; 
                            color: white; 
                            padding: 12px 24px; 
                            border: 1px solid #555; 
                            border-radius: 4px; 
                            cursor: not-allowed; 
                            font-size: 16px;
                            font-family: Segoe UI, sans-serif;
                            display: flex;
                            align-items: center;
                            gap: 12px;
                            width: 250px;
                            box-shadow: none;
                            opacity: 0.5;
                        ">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg" width="20">
                            <span>Logg inn med Microsoft</span>
                        </button>
                        <p style="font-size: 12px; color: #888; margin-top: 5px; text-align: center;">(Kun personlig Microsoft-konto, ikke jobb/skole)</p>
                    ''')

                # Combine in a container
                full_html = clean_html(f'''
                    <div style="display: flex; flex-direction: column; gap: 10px; align-items: center; margin-top: 20px;">
                        {google_btn}
                        {ms_btn}
                    </div>
                ''')

                st.markdown(full_html, unsafe_allow_html=True)
                
                # Version at the bottom (Login Screen)
                st.sidebar.markdown("---")
                try:
                    with open("version.txt", "r") as f:
                        version = f.read().strip()
                except FileNotFoundError:
                    version = "v2.2.5" # Fallback
                st.sidebar.caption(version)
                return

    # --- Main App (Only reached if logged in) ---
    
    # Logo in Sidebar
    # st.sidebar.caption("v1.7.2") # Moved to top
    st.sidebar.image(LOGO_URL, width=150)
    st.sidebar.title(get_text("title"))
    


    st.sidebar.title(get_text("navigation"))
    app_mode = st.sidebar.radio(get_text("navigation"), [get_text("home"), get_text("module_quiz"), get_text("module_ndla"), get_text("my_history")], label_visibility="collapsed")
    
    if app_mode == get_text("home"):
        st.write(f"{get_text('welcome')}, {st.session_state.get('user_name', '')} ({st.session_state.get('user_email', '')})!")
        
        st.markdown(get_text("welcome_message"))
        
    st.divider()
    
    if app_mode == get_text("module_quiz"):
        # Init cookie manager if needed for logout inside quiz generator
        if not cookie_manager:
             cookie_manager = stx.CookieManager(key="cm_quiz")
        render_quiz_generator(cookie_manager)
    elif app_mode == get_text("module_ndla"):
        render_ndla_viewer()
    elif app_mode == get_text("my_history"):
        st.header(f"📜 {get_text('my_history')}")
        
        user_email = st.session_state.get('user_email')
        if user_email:
            from storage import get_user_results
            history_df = get_user_results(user_email)
            
            if not history_df.empty:
                # Display specific columns as requested: Date, Topic, Score/Total
                # Rename columns for better display
                display_df = history_df[['timestamp', 'topic', 'score', 'total', 'percentage']]
                display_df.columns = ["Dato", "Emne", "Poeng", "Totalt", "Prosent"]
                
                # Format percentage
                display_df['Prosent'] = display_df['Prosent'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("Du har ingen lagrede resultater ennå.")
        else:
            st.warning("Du må være logget inn for å se historikk.")

    # Version at the bottom (Main App)
    st.sidebar.markdown("---")
    try:
        with open("version.txt", "r") as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = "v2.2.5" # Fallback
    st.sidebar.caption(version)

if __name__ == "__main__":
    main()
