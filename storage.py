import pandas as pd
import streamlit as st
from supabase import create_client, Client
import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text

@st.cache_resource
def init_connection():
    """Initializes a connection to Supabase."""
    try:
        # Try getting secrets from Streamlit secrets first
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except (FileNotFoundError, KeyError):
        # Fallback to environment variables (for GitHub Actions)
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
    if not url or not key:
        # If running in a script without st.secrets or env vars, this will fail gracefully or raise error
        raise ValueError("Missing Supabase credentials (SUPABASE_URL, SUPABASE_KEY)")

    return create_client(url, key)

# The following functions (init_db, get_setting, save_setting, get_content_hierarchy, save_result)
# would need to be updated to use the Supabase client instead of SQLAlchemy engine.
# However, the instruction only provided the change for init_connection and imports.
# Keeping them as is for now, but they will likely break without further modifications.

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        # Try getting secrets from Streamlit secrets first
        try:
            secrets = st.secrets["postgres"]
            host = secrets['host']
            port = secrets['port']
            dbname = secrets['dbname']
            user = secrets['user']
            password = secrets['password']
            sslmode = secrets['sslmode']
            sslrootcert = secrets['sslrootcert']
        except (FileNotFoundError, KeyError):
            # Fallback to environment variables (for GitHub Actions)
            host = os.environ.get("POSTGRES_HOST")
            port = os.environ.get("POSTGRES_PORT")
            dbname = os.environ.get("POSTGRES_DB")
            user = os.environ.get("POSTGRES_USER")
            password = os.environ.get("POSTGRES_PASSWORD")
            sslmode = "require" # Default for Aiven
            sslrootcert = "ca.pem" # Default for Aiven in this repo
            
        if not host or not user or not password:
             print("DEBUG: Missing database credentials")
             return None

        # Construct the connection string
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}&sslrootcert={sslrootcert}"
        
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        print(f"DEBUG: Database connection error: {e}")
        # st.error might fail if running headless, but print works
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
                        topic TEXT,
                        title TEXT,
                        content TEXT,
                        url TEXT,
                        source_id TEXT UNIQUE,
                        path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # Create settings table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """))
                
                # Create login_logs table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS login_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TEXT,
                        user_email TEXT,
                        user_name TEXT
                    );
                """))

                # Create user_permissions table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_permissions (
                        user_email TEXT PRIMARY KEY,
                        can_download BOOLEAN DEFAULT FALSE
                    );
                """))
                
                # Create energy_readings table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS energy_readings (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        device_id TEXT,
                        device_name TEXT,
                        power_w FLOAT,
                        energy_kwh FLOAT
                    );
                """))
                
                conn.commit()
        except Exception as e:
            print(f"DEBUG: Database init error: {e}")
            st.error(f"Database init error: {e}")

def get_setting(key, default_value=None):
    """Retrieves a setting value from the database."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT value FROM settings WHERE key = :key"), {"key": key})
                row = result.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            print(f"Error getting setting {key}: {e}")
    return default_value

def save_setting(key, value):
    """Saves a setting value to the database."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO settings (key, value) 
                    VALUES (:key, :value) 
                    ON CONFLICT (key) 
                    DO UPDATE SET value = :value
                """), {"key": key, "value": str(value)})
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving setting {key}: {e}")
    return False

@st.cache_data(ttl=3600)
def get_content_hierarchy():
    """
    Fetches all learning materials and builds a nested dictionary hierarchy.
    Returns: dict {Subject: {Level1: {Level2: ... {_articles: [rows]} ... }}}
    """
    # Force cache invalidation (v2.1.7 fix)
    engine = get_db_connection()
    if not engine:
        return {}
    
    conn = None # Initialize conn to None
    try:
        conn = engine.connect() # Get a connection from the engine
        # Use DISTINCT to prevent duplicates if any exist in the DB
        query = "SELECT DISTINCT * FROM learning_materials ORDER BY subject, path, title"
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
            get_all_results.clear()
            return category
        except Exception as e:
            st.error(f"Error saving to database: {e}")
            return None
    else:
        return None

def delete_results(result_ids=None, user_email=None, topic=None):
    """
    Deletes results based on criteria.
    result_ids: list of IDs to delete
    user_email: delete all results for this email
    topic: delete all results for this topic (can be combined with user_email)
    """
    engine = get_db_connection()
    if not engine:
        return False
        
    try:
        with engine.connect() as conn:
            if result_ids:
                # Delete specific IDs
                # Use tuple for IN clause, handle single item tuple quirk
                if len(result_ids) == 1:
                    ids_tuple = f"({result_ids[0]})"
                else:
                    ids_tuple = tuple(result_ids)
                
                query = f"DELETE FROM quiz_results WHERE id IN {ids_tuple}"
                conn.execute(text(query))
                conn.commit()
                get_all_results.clear()
                return True
                
            elif user_email:
                if topic:
                    conn.execute(text("DELETE FROM quiz_results WHERE user_email = :email AND topic = :topic"), 
                                {"email": user_email, "topic": topic})
                else:
                    conn.execute(text("DELETE FROM quiz_results WHERE user_email = :email"), 
                                {"email": user_email})
                conn.commit()
                get_all_results.clear()
                return True
                
            elif topic:
                 conn.execute(text("DELETE FROM quiz_results WHERE topic = :topic"), 
                                {"topic": topic})
                 conn.commit()
                 get_all_results.clear()
                 return True
                 
    except Exception as e:
        print(f"Error deleting results: {e}")
        return False
    return False

@st.cache_data(ttl=60)
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

def log_login(user_email, user_name):
    """Logs a user login event."""
    # Ensure table exists
    init_db()
    
    import pytz
    oslo_tz = pytz.timezone('Europe/Oslo')
    timestamp_str = datetime.now(oslo_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO login_logs (timestamp, user_email, user_name) 
                    VALUES (:timestamp, :email, :name)
                """), {
                    "timestamp": timestamp_str,
                    "email": user_email,
                    "name": user_name
                })
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging login: {e}")
    return False

def get_login_logs():
    """Retrieves all login logs."""
    init_db()
    engine = get_db_connection()
    if engine:
        try:
            query = "SELECT * FROM login_logs ORDER BY timestamp DESC"
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            st.error(f"Error reading login logs: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def get_user_results(user_email):
    """Retrieves quiz results for a specific user."""
    engine = get_db_connection()
    if engine:
        try:
            # Use parameterized query for security
            query = text("SELECT timestamp, topic, score, total, percentage, category FROM quiz_results WHERE user_email = :email ORDER BY id DESC")
            with engine.connect() as conn:
                result = conn.execute(query, {"email": user_email})
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except Exception as e:
            print(f"Error getting user results: {e}")
    return pd.DataFrame()

def get_user_permissions(user_email):
    """Checks if a user has download permissions."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT can_download FROM user_permissions WHERE user_email = :email"), {"email": user_email})
                row = result.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            print(f"Error getting permissions for {user_email}: {e}")
    return False

def grant_permission(user_email, can_download):
    """Updates or inserts user permission."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO user_permissions (user_email, can_download)
                    VALUES (:email, :can_download)
                    ON CONFLICT (user_email) 
                    DO UPDATE SET can_download = :can_download
                """), {"email": user_email, "can_download": can_download})
                conn.commit()
            return True
        except Exception as e:
            st.error(f"Error granting permission: {e}")
            return False
    return False

def save_energy_readings(readings):
    """Saves a list of energy readings to the database."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                for r in readings:
                    conn.execute(text("""
                        INSERT INTO energy_readings (timestamp, device_id, device_name, power_w, energy_kwh)
                        VALUES (:timestamp, :device_id, :device_name, :power_w, :energy_kwh)
                    """), {
                        "timestamp": r['timestamp'],
                        "device_id": r['id'],
                        "device_name": r['name'],
                        "power_w": r['power_w'],
                        "energy_kwh": r['energy_kwh']
                    })
                conn.commit()
            return True
        except Exception as e:
            st.error(f"Error saving energy readings: {e}")
            return False
    return False

def get_energy_readings():
    """Retrieves all energy readings."""
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                df = pd.read_sql("SELECT * FROM energy_readings ORDER BY timestamp DESC", conn)
                return df
        except Exception as e:
            st.error(f"Error fetching energy readings: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def get_all_permissions():
    """Retrieves all user permissions."""
    engine = get_db_connection()
    if engine:
        try:
            query = "SELECT * FROM user_permissions"
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            print(f"Error getting all permissions: {e}")
    return pd.DataFrame()
