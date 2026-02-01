# Design Document - DCS Web-Tac

## Project Goal
To create a web-based alternative to Tacview for analyzing DCS World flight logs and real-time telemetry.

## System Architecture
### 1. Data Collection Layer
- **DCS Export Script**: A Lua script (`Export.lua`) that hooks into DCS World events.
- **Python Telemetry Server**: Listens for UDP packets from DCS and stores them in SQLite.

### 2. Data Storage Layer
- **SQLite**: Stores sortie metadata and high-frequency telemetry points.

### 3. Backend Layer
- **FastAPI**: Provides RESTful APIs for retrieving sorties and telemetry data.

### 4. Frontend Layer (B/S)
- **Dashboard**: Sortie list and summary statistics.
- **Visualizer**: 3D playback of flight paths.

## Database Schema
### Sorties Table
- `id`: PK
- `mission_name`: String
- `aircraft`: String
- `start_time`: DateTime

### Telemetry Table
- `id`: PK
- `sortie_id`: FK
- `ts`: Float (offset from start)
- `lat, lon, alt`: Float
- `roll, pitch, yaw`: Float
- `u, v, w`: Velocities
