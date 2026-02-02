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
            map_name TEXT,
            parse_status TEXT DEFAULT 'queued'
        )
    ''')

    # Objects Table (aircraft/units)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sortie_id INTEGER,
            obj_id TEXT,
            name TEXT,
            type TEXT,
            coalition TEXT,
            pilot TEXT,
            raw TEXT,
            FOREIGN KEY (sortie_id) REFERENCES sorties (id)
        )
    ''')

    # Telemetry Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sortie_id INTEGER,
            obj_id TEXT,
            time_offset REAL,
            lat REAL, lon REAL, alt REAL,
            roll REAL, pitch REAL, yaw REAL,
            ias REAL, mach REAL,
            g_force REAL,
            fuel_remaining REAL,
            raw TEXT,
            FOREIGN KEY (sortie_id) REFERENCES sorties (id)
        )
    ''')

    # Parse Jobs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parse_jobs (
            id TEXT PRIMARY KEY,
            sortie_id INTEGER,
            file_name TEXT,
            status TEXT,
            progress_pct REAL,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Lightweight migrations
    cursor.execute("PRAGMA table_info(telemetry)")
    cols = {row[1] for row in cursor.fetchall()}
    if "obj_id" not in cols:
        cursor.execute("ALTER TABLE telemetry ADD COLUMN obj_id TEXT")
    if "raw" not in cols:
        cursor.execute("ALTER TABLE telemetry ADD COLUMN raw TEXT")

    cursor.execute("PRAGMA table_info(objects)")
    ocols = {row[1] for row in cursor.fetchall()}
    if "raw" not in ocols:
        cursor.execute("ALTER TABLE objects ADD COLUMN raw TEXT")

    cursor.execute("PRAGMA table_info(sorties)")
    scols = {row[1] for row in cursor.fetchall()}
    if "parse_status" not in scols:
        cursor.execute("ALTER TABLE sorties ADD COLUMN parse_status TEXT DEFAULT 'queued'")

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_sortie_obj_time ON telemetry(sortie_id, obj_id, time_offset)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_objects_sortie ON objects(sortie_id)")

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
