import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, text
import os

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        secrets = st.secrets["postgres"]
        # Construct the connection string
        # Note: We need to handle the SSL certificate path correctly
        # In Streamlit Cloud, we might need to write the CA cert to a temp file if it's not present
        # But for now, we assume ca.pem is in the root
        
        db_url = f"postgresql://{secrets['user']}:{secrets['password']}@{secrets['host']}:{secrets['port']}/{secrets['dbname']}?sslmode={secrets['sslmode']}&sslrootcert={secrets['sslrootcert']}"
        
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initializes the database table if it doesn't exist."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS quiz_results (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        user_email TEXT,
                        user_name TEXT,
                        topic TEXT,
                        score INTEGER,
                        total INTEGER,
                        percentage FLOAT,
                        category TEXT
                    );
                """))
                conn.commit()
        except Exception as e:
            st.error(f"Error initializing database: {e}")

def get_performance_category(percentage):
    if percentage <= 33:
        return "Lav"
    elif percentage <= 66:
        return "Middels"
    else:
        return "Høy"

def save_result(user_email, user_name, score, total, percentage, topic):
    category = get_performance_category(percentage)
    
    # Ensure table exists
    init_db()
    
    import pytz
    oslo_tz = pytz.timezone('Europe/Oslo')
    # Format as string to ensure exact time is stored
    timestamp_str = datetime.now(oslo_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    new_data = {
        "timestamp": timestamp_str,
        "user_email": user_email,
        "user_name": user_name,
        "topic": topic,
        "score": score,
        "total": total,
        "percentage": percentage,
        "category": category
    }
    
    df_new = pd.DataFrame([new_data])
    
    engine = get_db_connection()
    if engine:
        try:
            df_new.to_sql('quiz_results', engine, if_exists='append', index=False)
            return category
        except Exception as e:
            st.error(f"Error saving to database: {e}")
            return None
    else:
        return None

def get_all_results():
    """Retrieves all results from the database."""
    # Ensure table exists before querying
    init_db()
    
    engine = get_db_connection()
    if engine:
        try:
            query = "SELECT * FROM quiz_results ORDER BY timestamp DESC"
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            st.error(f"Error reading from database: {e}")
            return pd.DataFrame()
    return pd.DataFrame()
