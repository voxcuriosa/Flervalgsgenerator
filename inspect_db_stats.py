from storage import get_db_connection
from sqlalchemy import text
import pandas as pd

def inspect_stats():
    engine = get_db_connection()
    if not engine:
        return

    query = "SELECT subject, topic, COUNT(*) as count FROM learning_materials GROUP BY subject, topic ORDER BY subject, topic"
    df = pd.read_sql(query, engine)
    
    print(df.to_string())
    
    print("\n--- Total per Subject ---")
    query_total = "SELECT subject, COUNT(*) as count FROM learning_materials GROUP BY subject"
    df_total = pd.read_sql(query_total, engine)
    print(df_total.to_string())

if __name__ == "__main__":
    inspect_stats()
