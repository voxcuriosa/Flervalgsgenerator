from storage import get_db_connection
from sqlalchemy import text

def run_import():
    engine = get_db_connection()
    if not engine:
        print("Failed to connect to DB")
        return

    with engine.connect() as conn:
        # 1. Delete "Tibber puls", "Vann", "Bad", "Bad kjeller"
        print("Deleting 'Tibber puls', 'Vann', 'Bad', 'Bad kjeller'...")
        conn.execute(text("DELETE FROM energy_readings WHERE device_name = 'Tibber puls'"))
        conn.execute(text("DELETE FROM energy_readings WHERE device_name = 'Vann'"))
        conn.execute(text("DELETE FROM energy_readings WHERE device_name = 'Bad'"))
        conn.execute(text("DELETE FROM energy_readings WHERE device_name = 'Bad kjeller'"))
        
        # 2. Define Data
        # Map: Name -> ID
        devices = {
            "VVB": "cdcc332f-8002-4de1-845a-878407d3e291",
            "Varmepumpe": "601d8ba9-6a7f-4b2f-bdb0-2197f2b67942",
            "Casper": "6c8ce886-dc7a-4d7a-9df8-973fb81d9773",
            "Cornelius": "d2a29535-9bce-4f5b-bbac-49679f77332b",
            "Bad - Varmekabler": "eb4743d9-c91f-4d34-964b-2d8b7b234b74", 
            "Bad kjeller - Varmekabler": "1aa5f3c3-2aed-4829-95ee-d95b4fa57430",
            "Vindfang": "9fcfaccc-55d6-4da4-8d1d-68747ae0dd37",
            "Stue": "b8f70df7-825c-42b8-8ab8-20407914a84b",
            "Kjellergang": "b469fd72-a7ac-4b5c-8c7e-608aa5996d9d"
        }

        # Data Structure: Date -> {Device: Value}
        data = [
            # 2024 Start
            ("2024-01-01 00:00:00", {"VVB": 9647, "Varmepumpe": 443, "Casper": 3238}),
            
            # 2024
            # Corrected VVB, VP, Casper based on new image
            # VVB 1/4 and 1/5 calculated to give 243 consumption:
            # 1/3: 10486
            # 1/4: 10486 + 243 = 10729
            # 1/5: 10729 + 243 = 10972
            # 1/6: 381 (Meter reset handled in app logic)
            
            ("2024-02-01 00:00:00", {"VVB": 10133, "Varmepumpe": 871, "Casper": 3700, "Cornelius": 1114, "Bad - Varmekabler": 2904, "Bad kjeller - Varmekabler": 2326, "Vindfang": 66, "Kjellergang": 757, "Stue": 430}),
            ("2024-03-01 00:00:00", {"VVB": 10486, "Varmepumpe": 1180, "Casper": 4042, "Cornelius": 1115, "Bad - Varmekabler": 3072, "Bad kjeller - Varmekabler": 2465, "Vindfang": 76, "Kjellergang": 1013, "Stue": 434}),
            ("2024-04-01 00:00:00", {"VVB": 10729, "Varmepumpe": 1366, "Casper": 4190, "Cornelius": 1115, "Bad - Varmekabler": 3211, "Bad kjeller - Varmekabler": 2527, "Vindfang": 90, "Kjellergang": 1220, "Stue": 458}), 
            ("2024-05-01 00:00:00", {"VVB": 10972, "Varmepumpe": 1536, "Casper": 4253, "Cornelius": 1115, "Bad - Varmekabler": 3385, "Bad kjeller - Varmekabler": 2770, "Vindfang": 104, "Kjellergang": 1515, "Stue": 462}),
            ("2024-06-01 00:00:00", {"VVB": 381, "Varmepumpe": 1536, "Casper": 4253, "Cornelius": 1115, "Bad - Varmekabler": 3484, "Bad kjeller - Varmekabler": 2867, "Vindfang": 105, "Kjellergang": 1539, "Stue": 462}),
            ("2024-07-01 00:00:00", {"VVB": 713, "Varmepumpe": 1536, "Casper": 4253, "Cornelius": 1115, "Bad - Varmekabler": 3625, "Bad kjeller - Varmekabler": 3047, "Vindfang": 105, "Kjellergang": 1539, "Stue": 462}),
            ("2024-08-01 00:00:00", {"VVB": 1003, "Varmepumpe": 1536, "Casper": 4253, "Cornelius": 1115, "Bad - Varmekabler": 3728, "Bad kjeller - Varmekabler": 3193, "Vindfang": 105, "Kjellergang": 1539, "Stue": 462}),
            ("2024-09-01 00:00:00", {"VVB": 1303, "Varmepumpe": 1536, "Casper": 4253, "Cornelius": 1115, "Bad - Varmekabler": 3837, "Bad kjeller - Varmekabler": 3335, "Vindfang": 105, "Kjellergang": 1539, "Stue": 462}),
            ("2024-10-01 00:00:00", {"VVB": 1581, "Varmepumpe": 1552, "Casper": 4253, "Cornelius": 1115, "Bad - Varmekabler": 3972, "Bad kjeller - Varmekabler": 3500, "Vindfang": 105, "Kjellergang": 1539, "Stue": 472}),
            ("2024-11-01 00:00:00", {"VVB": 1893, "Varmepumpe": 1693, "Casper": 4276, "Cornelius": 1115, "Bad - Varmekabler": 4159, "Bad kjeller - Varmekabler": 3810, "Vindfang": 105, "Kjellergang": 1553, "Stue": 473}),
            ("2024-12-01 00:00:00", {"VVB": 2253, "Varmepumpe": 1965, "Casper": 4384, "Cornelius": 1115, "Bad - Varmekabler": 4388, "Bad kjeller - Varmekabler": 4202, "Vindfang": 105, "Kjellergang": 1560, "Stue": 473}),
            
            # 2025
            ("2025-01-01 00:00:00", {"VVB": 2722, "Varmepumpe": 2297, "Casper": 4610, "Cornelius": 0, "Bad - Varmekabler": 4619, "Bad kjeller - Varmekabler": 4615, "Vindfang": 105, "Kjellergang": 1584, "Stue": 485}), 
            ("2025-02-01 00:00:00", {"VVB": 3266, "Varmepumpe": 2689, "Casper": 4913, "Cornelius": 8, "Bad - Varmekabler": 4829, "Bad kjeller - Varmekabler": 5013, "Vindfang": 106, "Kjellergang": 1893, "Stue": 485}),
            ("2025-03-01 00:00:00", {"VVB": 3732, "Varmepumpe": 2950, "Casper": 5183, "Cornelius": 28, "Bad - Varmekabler": 4993, "Bad kjeller - Varmekabler": 5243, "Vindfang": 106, "Kjellergang": 2177, "Stue": 485}),
            ("2025-04-01 00:00:00", {"VVB": 4298, "Varmepumpe": 3144, "Casper": 5338, "Cornelius": 28, "Bad - Varmekabler": 5149, "Bad kjeller - Varmekabler": 5243, "Vindfang": 106, "Kjellergang": 2390, "Stue": 493}),
            ("2025-05-01 00:00:00", {"VVB": 4809, "Varmepumpe": 3271, "Casper": 5422, "Cornelius": 28, "Bad - Varmekabler": 5291, "Bad kjeller - Varmekabler": 5243, "Vindfang": 106, "Kjellergang": 2390, "Stue": 493}),
            ("2025-06-01 00:00:00", {"VVB": 5266, "Varmepumpe": 3330, "Casper": 5446, "Cornelius": 28, "Bad - Varmekabler": 5429, "Bad kjeller - Varmekabler": 5243, "Vindfang": 106, "Kjellergang": 2390, "Stue": 494}),
            ("2025-10-01 00:00:00", {"VVB": 6523, "Varmepumpe": 3352}),
            ("2025-11-01 00:00:00", {"VVB": 6958, "Varmepumpe": 3510}),
            ("2025-12-01 00:00:00", {"VVB": 7408, "Varmepumpe": 3728}),
        ]

        print("Importing readings...")
        count = 0
        for date, values in data:
            for name, value in values.items():
                dev_id = devices.get(name)
                if dev_id:
                    conn.execute(text("""
                        DELETE FROM energy_readings 
                        WHERE timestamp = :timestamp AND device_id = :device_id
                    """), {"timestamp": date, "device_id": dev_id})
                    
                    conn.execute(text("""
                        INSERT INTO energy_readings (timestamp, device_id, device_name, power_w, energy_kwh)
                        VALUES (:timestamp, :device_id, :device_name, 0, :energy_kwh)
                    """), {
                        "timestamp": date,
                        "device_id": dev_id,
                        "device_name": name,
                        "energy_kwh": value
                    })
                    count += 1
        
        conn.commit()
        print(f"Done! Imported {count} readings.")

if __name__ == "__main__":
    run_import()
