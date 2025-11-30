from storage import get_db_connection
from sqlalchemy import text

def clean_history():
    engine = get_db_connection()
    if not engine:
        print("No engine")
        return

    subjects_to_clean = ["Historie vg2", "Historie vg3", "Historie (PB)", "Sosiologi og sosialantropologi"]
    
    with engine.connect() as conn:
        for subject in subjects_to_clean:
            print(f"Cleaning {subject}...")
            conn.execute(text("DELETE FROM learning_materials WHERE subject = :subject"), {"subject": subject})
        conn.commit()
    
    print("Cleanup complete.")

if __name__ == "__main__":
    clean_history()
