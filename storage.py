import pandas as pd
import os
from datetime import datetime

RESULTS_FILE = "quiz_results.csv"

def get_performance_category(percentage):
    if percentage <= 33:
        return "Lav"
    elif percentage <= 66:
        return "Middels"
    else:
        return "Høy"

def save_result(user_email, user_name, score, total, percentage, topic):
    category = get_performance_category(percentage)
    
    new_data = {
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "User Email": [user_email],
        "User Name": [user_name],
        "Topic": [topic],
        "Score": [score],
        "Total": [total],
        "Percentage": [percentage],
        "Category": [category]
    }
    
    df_new = pd.DataFrame(new_data)
    
    if os.path.exists(RESULTS_FILE):
        df_existing = pd.read_csv(RESULTS_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(RESULTS_FILE, index=False)
    else:
        df_new.to_csv(RESULTS_FILE, index=False)
        
    return category
