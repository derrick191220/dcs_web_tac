# Design & Requirements Document - DCS Web‑Tac (Enterprise Edition)

> **Version**: v1.0 (self‑iterating)
> **Last Updated**: 2026‑02‑01
> **Owner**: Xiao Ou

This document is **actionable**: it defines scope, flows, API contracts, data models, non‑functional targets, and acceptance criteria. It is intended to directly guide implementation.

---

## 1. Vision & Goals
- Build a Tacview‑grade web analytics platform for DCS World replays.
- Provide high‑fidelity 3D playback, telemetry HUD, and analysis tools.
- Be stable, reproducible, and deployable (Render).

## 2. Core Principles
1. **Technical Excellence**: High‑performance backend (FastAPI) + expert‑level 3D (Cesium.js).
2. **Friendly UI**: Tailwind CSS, clear information hierarchy.
3. **Practical Functionality**: ACMI replay, mission browsing, flight metrics.
4. **Security & Reliability**: ACID storage and safe background processing.
5. **Aviation Standards**: ACMI 2.1/2.2 compliant.
6. **Documentation**: API docs + structured design spec.

---

## 3. User Stories (MVP)
1. **Upload a real ACMI** and see it listed as a sortie.
2. **Select an aircraft** from a sortie and replay its trajectory.
3. **See live HUD** data (altitude, speed, G, attitude) while timeline plays.
4. **Verify health** via built‑in diagnostics.

---

## 4. Functional Scope (V1)
### 4.1 Ingestion
- Upload `.acmi`, `.zip`, `.gz`, `.zip.acmi`.
- Background parse; store data in SQLite.
- Reject unsupported formats.

### 4.2 Data Browsing
- List sorties (most recent first).
- List aircraft objects within a sortie.
- Filter telemetry by aircraft (`obj_id`).

### 4.3 Playback
- Render aircraft position and orientation.
- Render full trail path.
- HUD updates based on nearest telemetry sample.

### 4.4 Diagnostics
- Local chain test (pytest + headless browser).
- Production scan with `doctor.py`.

---

## 5. Interaction Flows (Textual)
### 5.1 Upload Flow
1) User clicks **Upload ACMI**.
2) File picker opens → user selects ACMI.
3) Frontend sends `POST /api/upload`.
4) Backend queues parse in background.
5) Frontend reloads sortie list.

### 5.2 Playback Flow
1) User selects sortie.
2) Frontend loads aircraft list.
3) User selects aircraft.
4) Frontend loads telemetry (filtered by `obj_id`).
5) Viewer renders trajectory + HUD.

---

## 6. API Contracts (V1)
### `GET /api/`
**Response**
```json
{ "status": "DCS Web‑Tac Online", "version": "0.2.x" }
```

### `GET /api/sorties`
**Response**
```json
[
  {"id":1,"mission_name":"...","pilot_name":"...","aircraft_type":"...","start_time":"...","map_name":null}
]
```

### `GET /api/sorties/{id}/objects`
**Response**
```json
[
  {"id":10,"sortie_id":1,"obj_id":"b1100","name":"F‑16C_50","type":"Air+FixedWing","coalition":"Blue","pilot":"Blade"}
]
```

### `GET /api/sorties/{id}/telemetry?obj_id=...`
**Response**
```json
[
  {"obj_id":"b1100","time_offset":1.0,"lat":25.0,"lon":54.4,"alt":1000,
   "roll":0.1,"pitch":0.0,"yaw":180.0,"ias":350,"g_force":1.1}
]
```

### `POST /api/upload`
**Request**: multipart/form‑data (`file`)
**Response**
```json
{ "message": "Successfully uploaded <filename>" }
```

---

## 7. Data Model
### 7.1 Sorties
- id, mission_name, pilot_name, aircraft_type, start_time, map_name

### 7.2 Objects
- id, sortie_id, obj_id, name, type, coalition, pilot

### 7.3 Telemetry
- id, sortie_id, obj_id, time_offset
- lat, lon, alt
- roll, pitch, yaw
- ias, mach, g_force, fuel_remaining

---

## 8. Non‑Functional Targets
- **Upload size**: >= 100MB ACMI
- **Parse time**: < 60s for 100MB on Render
- **UI responsiveness**: < 200ms interaction latency
- **Browser errors**: 0 fatal console errors

---

## 9. Acceptance Criteria (V1)
- Upload works end‑to‑end; sortie appears in list.
- Aircraft selector shows all aircraft objects.
- Selecting aircraft updates HUD & path.
- No fatal console errors (local + Render).

---

## 10. Risk & Mitigation
- **Large files** → stream parse, batch insert.
- **Obj metadata missing** → fallback to obj_id display.
- **Cesium load delays** → robust initialization & retries.

---

## 11. Roadmap (Tacview Parity)
1) Timeline controls (play/pause/speed)
2) Event markers (kills/launches/impacts)
3) Charts (speed/alt/G)
4) Multi‑aircraft filters
5) Real‑time UDP ingestion

---

## 12. QA & Release
- Follow `docs/qa.md` (Xiao Ou Loop v2.0)

---

> Chinese version: `docs/DESIGN.zh.md`
