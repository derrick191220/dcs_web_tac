import sqlite3
import re
import os
import zipfile
import gzip
import io

class AcmiParser:
    def __init__(self, db_path='data/flight_data.db'):
        self.db_path = db_path
        self.sortie_id = None
        self.primary_obj_id = None
        self.objects = {}

    def _get_file_handle(self, acmi_path):
        if acmi_path.endswith('.zip') or acmi_path.endswith('.zip.acmi'):
            # Read .acmi content into memory to avoid closed zip handles
            with zipfile.ZipFile(acmi_path, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.acmi'):
                        data = z.read(name)
                        return io.StringIO(data.decode('latin-1'))
        elif acmi_path.endswith('.gz'):
            return io.TextIOWrapper(gzip.open(acmi_path, 'rb'), encoding='latin-1')
        else:
            return open(acmi_path, 'r', encoding='latin-1')

    def parse_file(self, acmi_path):
        if not os.path.exists(acmi_path):
            print(f"Error: {acmi_path} not found")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time_offset = 0.0
        mission_name = os.path.basename(acmi_path)
        pilot_name = "Unknown Pilot"
        aircraft_type = "Unknown"

        try:
            handle = self._get_file_handle(acmi_path)
            with handle as f:
                for line in f:
                    line = line.strip()
                    if not line: continue

                    if line.startswith('0,'):
                        if 'MissionTitle=' in line:
                            match = re.search(r'MissionTitle=([^,]*)', line)
                            if match: mission_name = match.group(1)
                        if 'RecordingPlayerName=' in line:
                            match = re.search(r'RecordingPlayerName=([^,]*)', line)
                            if match: pilot_name = match.group(1)
                        continue

                    if line.startswith('#'):
                        try:
                            current_time_offset = float(line[1:])
                        except ValueError:
                            continue
                        continue

                    if ',T=' in line:
                        parts = line.split(',', 1)
                        obj_id = parts[0]

                        # Parse key=value fields on the line
                        fields = {}
                        if len(parts) > 1:
                            for seg in parts[1].split(','):
                                if '=' in seg:
                                    k, v = seg.split('=', 1)
                                    fields[k] = v

                        obj_type = fields.get('Type')
                        obj_name = fields.get('Name')
                        obj_pilot = fields.get('Pilot')
                        obj_coal = fields.get('Coalition')

                        # Capture/refresh object metadata when available
                        if obj_type or obj_name or obj_pilot or obj_coal:
                            meta = self.objects.get(obj_id, {})
                            if obj_type: meta['type'] = obj_type
                            if obj_name: meta['name'] = obj_name
                            if obj_pilot: meta['pilot'] = obj_pilot
                            if obj_coal: meta['coalition'] = obj_coal
                            self.objects[obj_id] = meta

                        # Create sortie on first Air object
                        if self.sortie_id is None and (obj_type and obj_type.startswith('Air')):
                            aircraft_type = obj_name or aircraft_type
                            pilot_name = obj_pilot or pilot_name
                            cursor.execute(
                                'INSERT INTO sorties (mission_name, pilot_name, aircraft_type) VALUES (?, ?, ?)',
                                (mission_name, pilot_name, aircraft_type)
                            )
                            self.sortie_id = cursor.lastrowid

                        # Only store telemetry for Air objects
                        obj_meta = self.objects.get(obj_id, {})
                        if not (obj_meta.get('type') or obj_type):
                            continue
                        if not (obj_meta.get('type', obj_type).startswith('Air')):
                            continue

                        # Upsert object into objects table once
                        if self.sortie_id is not None and obj_id not in getattr(self, '_obj_written', set()):
                            self._obj_written = getattr(self, '_obj_written', set())
                            cursor.execute(
                                'INSERT INTO objects (sortie_id, obj_id, name, type, coalition, pilot) VALUES (?, ?, ?, ?, ?, ?)',
                                (self.sortie_id, obj_id, obj_meta.get('name') or obj_name, obj_meta.get('type') or obj_type,
                                 obj_meta.get('coalition') or obj_coal, obj_meta.get('pilot') or obj_pilot)
                            )
                            self._obj_written.add(obj_id)

                        t_match = re.search(r'T=([^,]*)', line)
                        if t_match:
                            coords = t_match.group(1).split('|')
                            def to_float(v):
                                try:
                                    return float(v) if v else 0.0
                                except ValueError:
                                    return 0.0

                            lon = to_float(coords[0]) if len(coords) > 0 else 0.0
                            lat = to_float(coords[1]) if len(coords) > 1 else 0.0
                            alt = to_float(coords[2]) if len(coords) > 2 else 0.0
                            roll = to_float(coords[3]) if len(coords) > 3 else 0.0
                            pitch = to_float(coords[4]) if len(coords) > 4 else 0.0
                            yaw = to_float(coords[5]) if len(coords) > 5 else 0.0
                            
                            ias = 0
                            ias_match = re.search(r'IAS=([^,]*)', line)
                            if ias_match: ias = float(ias_match.group(1))
                            
                            g_force = 1.0
                            g_match = re.search(r'G=([^,]*)', line)
                            if g_match: g_force = float(g_match.group(1))

                            cursor.execute('''
                                INSERT INTO telemetry (sortie_id, obj_id, time_offset, lat, lon, alt, roll, pitch, yaw, ias, g_force)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (self.sortie_id, obj_id, current_time_offset, lat, lon, alt, roll, pitch, yaw, ias, g_force))

            conn.commit()
            print(f"Successfully processed {acmi_path}")
        except Exception as e:
            print(f"Failed to parse {acmi_path}: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    import db_init
    db_init.init_db()
    parser = AcmiParser()
    # Testing with sample if exists
    sample_file = 'data/samples/full_flight_sim.acmi'
    if os.path.exists(sample_file):
        parser.parse_file(sample_file)
