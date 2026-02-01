import sqlite3
import os

def init_db(db_path='data/flight_data.db'):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sorties Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sorties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_name TEXT,
            pilot_name TEXT,
            aircraft_type TEXT,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            map_name TEXT
        )
    ''')
    
    # Telemetry Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sortie_id INTEGER,
            time_offset REAL,
            lat REAL, lon REAL, alt REAL,
            roll REAL, pitch REAL, yaw REAL,
            ias REAL, mach REAL,
            g_force REAL,
            fuel_remaining REAL,
            FOREIGN KEY (sortie_id) REFERENCES sorties (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
