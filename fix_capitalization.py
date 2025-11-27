from storage import get_db_connection
from sqlalchemy import text

def fix_title():
    conn = get_db_connection()
    if conn:
        try:
            with conn.connect() as connection:
                # Update the specific title
                query = text("""
                    UPDATE learning_materials 
                    SET title = 'Oversikt: Europeisk middelalder' 
                    WHERE title = 'Oversikt: europeisk middelalder'
                """)
                result = connection.execute(query)
                connection.commit()
                
                print(f"Updated {result.rowcount} row(s).")
                
                # Verify
                verify_query = text("SELECT title FROM learning_materials WHERE title = 'Oversikt: Europeisk middelalder'")
                verify_result = connection.execute(verify_query).fetchone()
                if verify_result:
                    print(f"Verification successful: {verify_result[0]}")
                else:
                    print("Verification failed.")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_title()
