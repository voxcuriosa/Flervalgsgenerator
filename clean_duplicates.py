from storage import get_db_connection
from sqlalchemy import text

def clean_duplicates():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect")
        return

    to_delete = [
        "Stue - Varmekabler ",
        "Bad kjeller - Varmekabler ",
        "Kjellergang - Varme",
        "Casper - Varme",
        "Cornelius - Varmekabler ",
        "Varmepumpe ",
        "Bad - Varmekabler ",
        "Vann ", 
        "Tibber puls",
        "CBV  (EHVKFY9X)",
        "Kjellerstue - Varmekabler ", # Assuming not needed or will be re-fetched if needed
        "Vaskerom - varme", # Assuming not needed
        "Kjellerstue - Varmeovn", # Assuming not needed
        "Cornelius - Varmekabler"
    ]
    
    with engine.connect() as conn:
        for name in to_delete:
            print(f"Deleting {name}...")
            conn.execute(text("DELETE FROM energy_readings WHERE device_name = :name"), {"name": name})
        conn.commit()
        print("Done cleaning.")

if __name__ == "__main__":
    clean_duplicates()
