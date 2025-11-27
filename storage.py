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
        print(f"DEBUG: Database connection error: {e}")
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initializes the database table if it doesn't exist."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                # Create quiz_results table if it doesn't exist
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS quiz_results (
                        id SERIAL PRIMARY KEY,
                        timestamp TEXT,
                        user_email TEXT,
                        user_name TEXT,
                        topic TEXT,
                        score INTEGER,
                        total INTEGER,
                        percentage FLOAT,
                        category TEXT
                    );
                """))
                
                # Create learning_materials table for NDLA content
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS learning_materials (
                        id SERIAL PRIMARY KEY,
                        subject TEXT,
                        topic TEXT,
                        title TEXT,
                        content TEXT,
                        url TEXT,
                        source_id TEXT UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()
        except Exception as e:
            st.error(f"Error initializing database: {e}")

def get_content_hierarchy():
    """
    Fetches all learning materials and builds a nested dictionary hierarchy.
    Returns: dict {Subject: {Level1: {Level2: ... {_articles: [rows]} ... }}}
    """
    engine = get_db_connection()
    if not engine:
        return {}
    
    conn = None # Initialize conn to None
    try:
        conn = engine.connect() # Get a connection from the engine
        query = "SELECT * FROM learning_materials ORDER BY subject, path, title"
        df = pd.read_sql(query, conn)
        
        hierarchy = {}
        
        for _, row in df.iterrows():
            subject = row['subject']
            path_str = row['path']
            
            if not path_str:
                path_parts = ["Diverse", row['topic']]
            else:
                path_parts = path_str.split(" > ")
                
            current_level = hierarchy.setdefault(subject, {})
            
            for part in path_parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
                
            if "_articles" not in current_level:
                current_level["_articles"] = []
            current_level["_articles"].append(row.to_dict())
            
        return hierarchy
    except Exception as e:
        print(f"Error fetching hierarchy: {e}")
        return {}
    finally:
        if conn: # Ensure conn is not None before closing
            conn.close()

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
