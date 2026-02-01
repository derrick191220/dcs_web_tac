# Design Document - DCS Web‑Tac (Enterprise Edition)

## 1. Vision & Goals
- Build a Tacview‑grade web analytics platform for DCS World replays.
- Provide high‑fidelity 3D playback, telemetry HUD, and analysis tools.
- Be stable, reproducible, and deployable (Render).

## 2. Core Principles
1. **Technical Excellence**: High‑performance asynchronous backend (FastAPI) and expert‑level 3D visualization (Cesium.js).
2. **Friendly UI**: Interactive dashboards with Tailwind CSS and deep data integration.
3. **Practical Functionality**: ACMI replay, mission browsing, and flight performance metrics.
4. **Security & Reliability**: ACID storage via SQLite and background task processing.
5. **Aviation Standards**: Compliant with ACMI 2.1/2.2 and DCS conventions.
6. **Documentation**: Integrated API docs and structured design specs.

## 3. Scope (MVP)
- Upload ACMI (.acmi/.zip/.gz/.zip.acmi)
- Parse ACMI and store in SQLite
- List sorties and aircraft objects
- Select aircraft and replay trajectory + HUD
- Health checks and diagnostics

## 4. Data Model
### 4.1 Sorties
- id, mission_name, pilot_name, aircraft_type, start_time, map_name

### 4.2 Objects
- id, sortie_id, obj_id, name, type, coalition, pilot

### 4.3 Telemetry
- id, sortie_id, obj_id, time_offset
- lat, lon, alt
- roll, pitch, yaw
- ias, mach, g_force, fuel_remaining

## 5. Backend APIs (v0)
- `GET /api/` → health
- `GET /api/sorties`
- `GET /api/sorties/{id}/objects`
- `GET /api/sorties/{id}/telemetry?obj_id=...`
- `POST /api/upload`

## 6. Frontend UX
- Left: sorties list + aircraft selector
- Center: Cesium 3D globe and flight path
- Right: HUD (altitude/speed/G/attitude)
- Upload button (ACMI)

## 7. Rendering & Playback
- Use Cesium `SampledPositionProperty` for smooth interpolation
- Model orientation uses ACMI yaw/pitch/roll (degree)
- Path is persistent trail (full mission)

## 8. Performance Constraints
- Large ACMI files: stream/parse and store efficiently
- Avoid UI stutters: pre‑sample or batch rendering for large datasets

## 9. Roadmap (Tacview parity)
- Multi‑aircraft filters (type/coalition/pilot)
- Timeline controls (play/pause/speed)
- Event markers (kills, launches, impacts)
- Charts (speed/alt/G)
- Real‑time UDP ingestion

## 10. QA & Release
- Follow `docs/qa.md` (Xiao Ou Loop v2.0)

---

> Chinese version: `docs/DESIGN.zh.md`
