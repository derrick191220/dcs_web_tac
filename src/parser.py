import sqlite3
import re
import os
import zipfile
import gzip
import io
import json

class AcmiParser:
    def __init__(self, db_path='data/flight_data.db'):
        self.db_path = db_path
        self.sortie_id = None
        self.primary_obj_id = None
        self.objects = {}

    def _get_file_handle(self, acmi_path):
        if acmi_path.endswith('.zip') or acmi_path.endswith('.zip.acmi'):
            with zipfile.ZipFile(acmi_path, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.acmi'):
                        data = z.read(name)
                        return io.StringIO(data.decode('utf-8', errors='replace')), len(data)
        elif acmi_path.endswith('.gz'):
            fh = io.TextIOWrapper(gzip.open(acmi_path, 'rb'), encoding='utf-8', errors='replace')
            return fh, os.path.getsize(acmi_path)
        else:
            return open(acmi_path, 'r', encoding='utf-8', errors='replace'), os.path.getsize(acmi_path)

    def parse_file(self, acmi_path, job_id=None):
        if not os.path.exists(acmi_path):
            print(f"Error: {acmi_path} not found")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time_offset = 0.0
        mission_name = os.path.basename(acmi_path)
        pilot_name = "Unknown Pilot"
        aircraft_type = "Unknown"
        reference_time = None
        global_props_buffer = []

        def update_job(status=None, progress=None, error=None, sortie_id=None):
            if not job_id:
                return
            sets = []
            params = []
            if status is not None:
                sets.append("status = ?")
                params.append(status)
            if progress is not None:
                sets.append("progress_pct = ?")
                params.append(progress)
            if error is not None:
                sets.append("error = ?")
                params.append(error)
            if sortie_id is not None:
                sets.append("sortie_id = ?")
                params.append(sortie_id)
            if not sets:
                return
            sets.append("updated_at = CURRENT_TIMESTAMP")
            params.append(job_id)
            cursor.execute(f"UPDATE parse_jobs SET {', '.join(sets)} WHERE id = ?", params)
            conn.commit()

        try:
            handle, total_bytes = self._get_file_handle(acmi_path)
            processed_bytes = 0
            last_progress = -1
            update_job(status="running", progress=0)
            with handle as f:
                for i, line in enumerate(f):
                    processed_bytes += len(line.encode('latin-1', errors='ignore'))
                    if total_bytes:
                        progress = int(processed_bytes * 100 / total_bytes)
                        if progress != last_progress and progress % 5 == 0:
                            update_job(progress=progress)
                            last_progress = progress

                    line = line.strip()
                    if not line: continue

                    if line.startswith('0,'):
                        # Global properties & events
                        if 'ReferenceTime=' in line:
                            match = re.search(r'ReferenceTime=([^,]*)', line)
                            if match: reference_time = match.group(1)
                        if 'MissionTitle=' in line:
                            match = re.search(r'MissionTitle=([^,]*)', line)
                            if match: mission_name = match.group(1)
                        if 'RecordingPlayerName=' in line:
                            match = re.search(r'RecordingPlayerName=([^,]*)', line)
                            if match: pilot_name = match.group(1)

                        try:
                            kvs = line.split(',', 1)[1].split(',')
                            for seg in kvs:
                                if '=' in seg:
                                    k, v = seg.split('=', 1)
                                    # Event handling
                                    if k == 'Event':
                                        parts = v.split('|')
                                        event_type = parts[0] if parts else ''
                                        obj_ids = [p for p in parts[1:-1] if p]
                                        text = parts[-1] if parts else ''
                                        if self.sortie_id:
                                            cursor.execute(
                                                "INSERT INTO events (sortie_id, time_offset, event_type, object_ids, text, raw) VALUES (?, ?, ?, ?, ?, ?)",
                                                (self.sortie_id, current_time_offset, event_type, json.dumps(obj_ids), text, json.dumps({"Event": v}))
                                            )
                                        else:
                                            global_props_buffer.append(("Event", v))
                                    else:
                                        if self.sortie_id:
                                            cursor.execute(
                                                "INSERT INTO global_props (sortie_id, key, value) VALUES (?, ?, ?)",
                                                (self.sortie_id, k, v)
                                            )
                                        else:
                                            global_props_buffer.append((k, v))
                        except Exception:
                            pass
                        continue

                    if line.startswith('#'):
                        try:
                            current_time_offset = float(line[1:])
                        except ValueError:
                            continue
                        continue

                    if line.startswith('-'):
                        # object removal
                        if self.sortie_id:
                            cursor.execute(
                                "INSERT INTO events (sortie_id, time_offset, event_type, object_ids, text, raw) VALUES (?, ?, ?, ?, ?, ?)",
                                (self.sortie_id, current_time_offset, "Removed", json.dumps([line[1:]]), "", json.dumps({"Removed": line[1:]}))
                            )
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
                        obj_callsign = fields.get('CallSign')
                        obj_color = fields.get('Color')
                        obj_shape = fields.get('Shape')

                        # Capture/refresh object metadata when available
                        if obj_type or obj_name or obj_pilot or obj_coal:
                            meta = self.objects.get(obj_id, {})
                            if obj_type: meta['type'] = obj_type
                            if obj_name: meta['name'] = obj_name
                            if obj_pilot: meta['pilot'] = obj_pilot
                            if obj_coal: meta['coalition'] = obj_coal
                            if obj_callsign: meta['callsign'] = obj_callsign
                            if obj_color: meta['color'] = obj_color
                            if obj_shape: meta['shape'] = obj_shape
                            self.objects[obj_id] = meta

                        # Create sortie on first Air object
                        if self.sortie_id is None and (obj_type and obj_type.startswith('Air')):
                            aircraft_type = obj_name or aircraft_type
                            pilot_name = obj_pilot or pilot_name
                            cursor.execute(
                                "INSERT INTO sorties (mission_name, pilot_name, aircraft_type, parse_status, reference_time) VALUES (?, ?, ?, ?, ?)",
                                (mission_name, pilot_name, aircraft_type, "running", reference_time)
                            )
                            self.sortie_id = cursor.lastrowid
                            update_job(sortie_id=self.sortie_id)
                            # flush buffered global props/events
                            for k, v in global_props_buffer:
                                if k == "Event":
                                    parts = v.split('|')
                                    event_type = parts[0] if parts else ''
                                    obj_ids = [p for p in parts[1:-1] if p]
                                    text = parts[-1] if parts else ''
                                    cursor.execute(
                                        "INSERT INTO events (sortie_id, time_offset, event_type, object_ids, text, raw) VALUES (?, ?, ?, ?, ?, ?)",
                                        (self.sortie_id, 0.0, event_type, json.dumps(obj_ids), text, json.dumps({"Event": v}))
                                    )
                                else:
                                    cursor.execute(
                                        "INSERT INTO global_props (sortie_id, key, value) VALUES (?, ?, ?)",
                                        (self.sortie_id, k, v)
                                    )
                            global_props_buffer.clear()

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
                                'INSERT INTO objects (sortie_id, obj_id, name, type, coalition, pilot, callsign, color, shape, raw) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                (self.sortie_id, obj_id, obj_meta.get('name') or obj_name, obj_meta.get('type') or obj_type,
                                 obj_meta.get('coalition') or obj_coal, obj_meta.get('pilot') or obj_pilot,
                                 obj_meta.get('callsign') or obj_callsign, obj_meta.get('color') or obj_color,
                                 obj_meta.get('shape') or obj_shape,
                                 json.dumps(obj_meta, ensure_ascii=False))
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
                            u = to_float(coords[6]) if len(coords) > 6 else None
                            v = to_float(coords[7]) if len(coords) > 7 else None
                            heading = to_float(coords[8]) if len(coords) > 8 else None
                            
                            ias = 0
                            ias_match = re.search(r'IAS=([^,]*)', line)
                            if ias_match: ias = float(ias_match.group(1))
                            
                            g_force = 1.0
                            g_match = re.search(r'G=([^,]*)', line)
                            if g_match: g_force = float(g_match.group(1))

                            raw_payload = {
                                "T": coords,
                                **fields
                            }

                            cursor.execute('''
                                INSERT INTO telemetry (sortie_id, obj_id, time_offset, lat, lon, alt, roll, pitch, yaw, u, v, heading, ias, g_force, raw)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (self.sortie_id, obj_id, current_time_offset, lat, lon, alt, roll, pitch, yaw, u, v, heading, ias, g_force,
                                  json.dumps(raw_payload, ensure_ascii=False)))

            if self.sortie_id is not None:
                cursor.execute("UPDATE sorties SET parse_status = 'done' WHERE id = ?", (self.sortie_id,))
                conn.commit()
            update_job(status="done", progress=100)
            print(f"Successfully processed {acmi_path}")
        except Exception as e:
            update_job(status="failed", error=str(e))
            if self.sortie_id is not None:
                cursor.execute("UPDATE sorties SET parse_status = 'failed' WHERE id = ?", (self.sortie_id,))
                conn.commit()
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
