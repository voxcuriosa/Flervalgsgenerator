import openai
import json
import streamlit as st

def generate_quiz(text, num_questions, num_options, multiple_correct, language="no"):
    """
    Generates a quiz using OpenAI API.
    """
    
    # Check for API key
    if "openai" not in st.secrets or "api_key" not in st.secrets["openai"]:
        return {"error": "OpenAI API Key not found in secrets."}
        
    client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])
    # Define language string
    lang_str = "Norwegian"
    if language == "en":
        lang_str = "English"
    elif language == "ar":
        lang_str = "Arabic"
    elif language == "so":
        lang_str = "Somali"
    elif language == "ti":
        lang_str = "Tigrinya"
    elif language == "uk":
        lang_str = "Ukrainian"
    elif language == "th":
        lang_str = "Thai"
        
    prompt = f"""
    Generate {num_questions} multiple choice questions based on the text provided below.
    The questions should be in {lang_str}.
    
    For each question:
    - Provide {num_options} options.
    - If 'multiple_correct' is {multiple_correct}, allow up to 2 correct answers. Otherwise, exactly one correct answer.
    - Provide a short justification for the correct answer(s).
    - Ensure the output is valid JSON.
    
    Text:
    {text[:15000]} 
    """
    # Truncating text to ~15k chars to avoid token limits for now. 
    # In a real app, we might need chunking or RAG.
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Reverted to gpt-4o for speed
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates quizzes in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Enforce exact number of questions
        if "questions" in data:
            data["questions"] = data["questions"][:num_questions]
            
        return data
        
    except Exception as e:
        return {"error": str(e)}
