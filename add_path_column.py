from storage import get_db_connection
from sqlalchemy import text

def add_path_column():
    engine = get_db_connection()
    if engine:
        try:
            with engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='learning_materials' AND column_name='path'"))
                if not result.fetchone():
                    print("Adding 'path' column...")
                    conn.execute(text("ALTER TABLE learning_materials ADD COLUMN path TEXT"))
                    conn.commit()
                    print("Column added successfully.")
                else:
                    print("'path' column already exists.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    add_path_column()
