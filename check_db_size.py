from storage import get_db_connection
from sqlalchemy import text

def check_size():
    conn = get_db_connection()
    if conn:
        try:
            with conn.connect() as connection:
                # Get table size
                result = connection.execute(text("SELECT pg_size_pretty(pg_total_relation_size('learning_materials'))"))
                table_size = result.fetchone()[0]
                
                # Get exact bytes for more precision if needed
                result_bytes = connection.execute(text("SELECT pg_total_relation_size('learning_materials')"))
                table_bytes = result_bytes.fetchone()[0]
                table_mb = table_bytes / (1024 * 1024)
                
                # Get row count
                result_count = connection.execute(text("SELECT count(*) FROM learning_materials"))
                count = result_count.fetchone()[0]
                
                print(f"Table: learning_materials")
                print(f"Rows: {count}")
                print(f"Size (Pretty): {table_size}")
                print(f"Size (MB): {table_mb:.4f} MB")
                
        except Exception as e:
            print(f"Error querying database: {e}")
    else:
        print("Failed to connect to database.")

if __name__ == "__main__":
    check_size()
