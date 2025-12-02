from storage import get_db_connection
from sqlalchemy import text
from datetime import datetime

def insert_manual():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect")
        return

    # IDs
    vvb_id = "cdcc332f-8002-4de1-845a-878407d3e291"
    vp_id = "601d8ba9-6a7f-4b2f-bdb0-2197f2b67942"
    
    # Values
    vvb_val = 7408
    vp_val = 3728
    
    # Timestamp: Now
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with engine.connect() as conn:
        print(f"Inserting VVB: {vvb_val} at {now}")
        conn.execute(text("""
            INSERT INTO energy_readings (timestamp, device_id, device_name, power_w, energy_kwh)
            VALUES (:ts, :id, :name, 0, :val)
        """), {"ts": now, "id": vvb_id, "name": "VVB", "val": vvb_val})
        
        print(f"Inserting Varmepumpe: {vp_val} at {now}")
        conn.execute(text("""
            INSERT INTO energy_readings (timestamp, device_id, device_name, power_w, energy_kwh)
            VALUES (:ts, :id, :name, 0, :val)
        """), {"ts": now, "id": vp_id, "name": "Varmepumpe", "val": vp_val})
        
        conn.commit()
        print("Done.")

if __name__ == "__main__":
    insert_manual()
