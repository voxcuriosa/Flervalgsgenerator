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
    
    lang_instruction = "Language: Norwegian." if language == "no" else "Language: English."
    
    prompt = f"""
    Generate {num_questions} multiple choice questions based on the following text.
    
    Constraints:
    - {lang_instruction}
    - Each question should have {num_options} options.
    - {"If multiple options can be correct: Randomly vary between providing 1 or 2 correct answers per question. NEVER provide more than 2 correct answers." if multiple_correct else "Only one option should be correct."}
    - Options should be plausible and similar in length/style.
    - Provide a short justification for why the correct answer(s) is/are correct.
    - Return the output strictly as a JSON object with the following structure:
    
    {{
        "questions": [
            {{
                "question": "Question text here",
                "options": ["Option 1", "Option 2", ...],
                "correct_indices": [0] (List of indices of correct options, 0-indexed),
                "justification": "Explanation here"
            }},
            ...
        ]
    }}
    
    Text content:
    {text[:15000]} 
    """
    # Truncating text to ~15k chars to avoid token limits for now. 
    # In a real app, we might need chunking or RAG.
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or gpt-3.5-turbo-1106 for JSON mode
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
