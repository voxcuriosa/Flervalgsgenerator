from storage import get_db_connection
from sqlalchemy import text
import import_full_history

def run_reset_and_import():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    with engine.connect() as conn:
        # 1. Truncate table
        print("Truncating 'energy_readings' table...")
        conn.execute(text("TRUNCATE TABLE energy_readings"))
        conn.commit()
        
    # 2. Run Import
    print("Running full import...")
    import_full_history.run_import()

if __name__ == "__main__":
    run_reset_and_import()
