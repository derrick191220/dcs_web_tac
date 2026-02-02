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

**Reference baseline**: Tacview **1.9.5** (current) and **1.9.6 Beta 1** (latest beta) per Tacview official documentation index (updated 2023‑07‑14).

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
### 4.1 Ingestion (with progress)
- Upload `.acmi`, `.zip`, `.gz`, `.zip.acmi`.
- Create **Parse Job** with status (`queued/running/done/failed`).
- Progress updates: bytes processed / total, ETA (best effort).
- Completion prompt: visible UI toast + sortie list refresh.
- Reject unsupported formats with clear error.

### 4.2 Data Browsing (Tacview‑like)
- Sortie list (time, mission, pilot, aircraft, map).
- Aircraft list with filters: **type/coalition/pilot/name**.
- Quick search by callsign/pilot.
- Telemetry query supports **time window** and **downsample**.

### 4.3 Playback (Tacview‑like)
- Timeline controls: play/pause/seek/speed (0.5x–8x).
- View modes: **follow aircraft / free camera / top‑down**.
- HUD panels: altitude, IAS, G, attitude.
- Trajectory: full trail + recent trail toggle.

### 4.4 Accuracy Assurance (Replay correctness)
- Units/coordinate validation on ingest (WGS‑84, meters, knots, degrees).
- Time base aligned to `ReferenceTime` + `time_offset` seconds.
- Orientation sanity checks (yaw continuity, pitch/roll limits).
- Optional **ground truth** sampling: compare rendered positions vs raw telemetry.

## 4.5 3D Model Attitude Drive (How it works)
- Each telemetry point provides **lat/lon/alt + yaw/pitch/roll** in degrees.
- Cesium pipeline:
  1) `SampledPositionProperty` for position (time‑stamped)
  2) `SampledProperty(Quaternion)` for orientation
  3) `Transforms.headingPitchRollQuaternion(position, HPR)` to produce orientation
- The 3D model is updated by Cesium per timeline tick (no manual interpolation).

## 4.6 Why Earlier Attitude Was Incorrect (Root cause)
- Wrong assumption about ACMI angle conventions (NED vs ENU).
- Model forward axis not explicitly calibrated (needed yaw offset).
- No visual reference axes or validation harness to catch drift.

## 4.7 Improvements to Guarantee Accuracy
- Fix and lock **angle conventions** (ACMI yaw/pitch/roll → Cesium HPR) in docs + code.
- Add **model axis calibration** (yawOffset/pitchSign/rollSign constants per model).
- Add **visual attitude axes** (debug overlay) and **numeric verification** HUD.
- Add **automated attitude checks**: max delta between consecutive frames; log anomalies.
- Add **reference scenario tests** (straight flight, 90° roll, climb) to validate.

### 4.5 Diagnostics
- Local chain test (pytest + headless browser).
- Production scan with `doctor.py` + last parse status.

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

## 6. Frontend UX/UI Design (V1)
### 6.1 Layout
- **Header**: project name, current aircraft, upload button, status indicator (parse job).
- **Left Panel**: sortie list + filters + aircraft selector.
- **Center**: Cesium 3D viewer + timeline controls.
- **Right Panel**: HUD cards (altitude, IAS, G, attitude) + mini‑charts (optional).

### 6.2 Key Components
- **Upload ACMI Modal**: file picker, progress bar, status (queued/running/done/failed).
- **Sortie List**: mission name, time, pilot, aircraft, map.
- **Aircraft Selector**: dropdown + search (pilot/callsign).
- **Timeline**: play/pause, speed (0.5x–8x), scrubber, current time.
- **View Mode Toggle**: follow / free / top‑down.
- **HUD**: altitude, IAS, G, roll/pitch/yaw, lat/lon.

### 6.3 Interaction Rules
- Upload → create job → show progress toast → refresh sorties on completion.
- Selecting sortie loads aircraft list; selecting aircraft loads telemetry.
- Timeline scrub updates HUD + model pose synchronously.
- Empty states for no sorties / no aircraft / no telemetry.

### 6.4 Visual Style
- Dark aviation theme, high contrast.
- Typography: compact numeric display for instruments.
- Colors: Blue (friendly), Red (hostile), Yellow (current track).

## 7. Engineering Standards & Compliance
- **ACMI 2.1/2.2**: Field parsing, time semantics, object metadata, and coordinate handling must follow Tacview ACMI spec.
- **Coordinate Standard**: WGS‑84 geodetic lat/lon (deg), altitude MSL (meters).
- **Attitude Standard**: roll/pitch/yaw in degrees (right‑handed), converted to Cesium HPR.
- **Unit Standard**: IAS in knots, altitude meters, time in seconds.
- **Data Integrity**: never drop records silently; invalid fields default to 0 and log warnings.
- **Traceability**: each parse creates a job record with status, duration, and error reason.

## 7. API Contracts (V1)
### Error Schema (all endpoints)
```json
{ "error": "string", "details": {"field": "reason"} }
```

### `GET /api/`
**Response**
```json
{ "status": "DCS Web‑Tac Online", "version": "0.2.x" }
```

### `GET /api/sorties`
**Response**
```json
[
  {"id":1,"mission_name":"...","pilot_name":"...","aircraft_type":"...","start_time":"...","map_name":null,
   "parse_status":"done"}
]
```

### `GET /api/sorties/{id}/objects`
**Response**
```json
[
  {"id":10,"sortie_id":1,"obj_id":"b1100","name":"F‑16C_50","type":"Air+FixedWing","coalition":"Blue","pilot":"Blade"}
]
```

### `GET /api/sorties/{id}/telemetry`
**Query Params**: `obj_id`, `start`, `end`, `downsample`, `limit`
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
{ "message": "Successfully uploaded <filename>", "job_id": "abc123" }
```

### `GET /api/jobs/{id}`
```json
{ "id":"abc123", "sortie_id":1, "status":"running", "progress_pct":42, "error":null }
```

### `GET /api/jobs/{id}/events`
```json
[{"ts":1700000000,"level":"info","message":"Parsing ACMI chunk 12/60"}]
```

---

## 8. Data Model
### 8.1 Sorties
- id, mission_name, pilot_name, aircraft_type, start_time, map_name, parse_status

### 8.2 Objects
- id, sortie_id, obj_id, name, type, coalition, pilot

### 8.3 Telemetry
- id, sortie_id, obj_id, time_offset
- lat, lon, alt
- roll, pitch, yaw
- ias, mach, g_force, fuel_remaining

### 8.4 Parse Jobs
- id, sortie_id, status, progress_pct, error, created_at, updated_at

---

## 9. Tech Stack & Authority
- **Cesium.js**: industry‑standard 3D globe/trajectory engine (geospatial + aviation usage)
- **FastAPI**: modern high‑performance API framework (Python ecosystem standard)
- **ACMI (Tacview)**: de‑facto standard for flight replay data
- **Diagnostics**: pytest + Playwright + doctor.py

## 10. Technical Challenges & Mitigations
1. **Huge telemetry volume** → windowed queries + downsampling + indexes
2. **Large upload parsing** → background jobs + progress tracking + chunked parse
3. **Cesium performance** → decimated samples + lazy rendering
4. **Time/Unit correctness** → strict unit conversion + validation
5. **Multi‑aircraft filtering** → object index + server‑side filters
6. **Render cold starts** → robust init + retry logic

## 11. Non‑Functional Targets
- **Upload size**: >= 100MB ACMI
- **Parse time**: < 60s for 100MB on Render
- **UI responsiveness**: < 200ms interaction latency
- **Browser errors**: 0 fatal console errors
- **Telemetry access**: supports windowed query and downsampling
- **Indexes**: telemetry(sortie_id,obj_id,time_offset), objects(sortie_id)
- **Security**: upload size limit, content‑type allowlist, optional token auth

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

## 13. Self‑Review Checklist (Doc Quality)
- ✅ Reference Tacview official docs (version baseline recorded)
- ✅ API contracts include errors and parameters
- ✅ Units/time semantics explicitly defined
- ✅ Performance targets and indexes specified
- ✅ Acceptance criteria are testable

---

> Chinese version: `docs/DESIGN.zh.md`
