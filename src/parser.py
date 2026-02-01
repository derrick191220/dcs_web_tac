import sqlite3
import re
import os

class AcmiParser:
    def __init__(self, db_path='data/flight_data.db'):
        self.db_path = db_path
        self.sortie_id = None

    def parse_file(self, acmi_path):
        if not os.path.exists(acmi_path):
            print(f"Error: {acmi_path} not found")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time_offset = 0.0
        mission_name = "Unknown Mission"
        pilot_name = "Unknown Pilot"
        aircraft_type = "Unknown"

        with open(acmi_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue

                # 1. Parse Global Info (Sortie Metadata)
                if line.startswith('0,'):
                    if 'MissionTitle=' in line:
                        mission_name = re.search(r'MissionTitle=([^,]*)', line).group(1)
                    if 'RecordingPlayerName=' in line:
                        pilot_name = re.search(r'RecordingPlayerName=([^,]*)', line).group(1)
                    continue

                # 2. Parse Time Frame
                if line.startswith('#'):
                    current_time_offset = float(line[1:])
                    continue

                # 3. Parse Object Telemetry (Simplified for POC)
                # Example: 1,T=lat|lon|alt|roll|pitch|yaw,Name=F-16C...
                if ',T=' in line:
                    obj_id = line.split(',')[0]
                    # We only care about the primary aircraft (usually ID 1 or first seen)
                    if not self.sortie_id:
                        if 'Name=' in line:
                            aircraft_type = re.search(r'Name=([^,]*)', line).group(1)
                        
                        cursor.execute('INSERT INTO sorties (mission_name, pilot_name, aircraft_type) VALUES (?, ?, ?)',
                                     (mission_name, pilot_name, aircraft_type))
                        self.sortie_id = cursor.lastrowid

                    # Extract Transformation Data
                    t_match = re.search(r'T=([^,]*)', line)
                    if t_match:
                        coords = t_match.group(1).split('|')
                        # ACMI format: lon|lat|alt|roll|pitch|yaw
                        lon = float(coords[0]) if len(coords) > 0 and coords[0] else 0
                        lat = float(coords[1]) if len(coords) > 1 and coords[1] else 0
                        alt = float(coords[2]) if len(coords) > 2 and coords[2] else 0
                        
                        # Extract additional metrics
                        ias = 0
                        ias_match = re.search(r'IAS=([^,]*)', line)
                        if ias_match: ias = float(ias_match.group(1))
                        
                        g_force = 1.0
                        g_match = re.search(r'G=([^,]*)', line)
                        if g_match: g_force = float(g_match.group(1))

                        cursor.execute('''
                            INSERT INTO telemetry (sortie_id, time_offset, lat, lon, alt, ias, g_force)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (self.sortie_id, current_time_offset, lat, lon, alt, ias, g_force))

        conn.commit()
        conn.close()
        print(f"Successfully imported {acmi_path} into database.")

if __name__ == "__main__":
    # Ensure DB is initialized
    from db_init import init_db
    init_db()
    
    parser = AcmiParser()
    parser.parse_file('data/samples/real_flight.acmi')
