# How to run DCS Web-Tac

## Prerequisites
- Python 3.10+ installed on your system.

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/derrick191220/dcs_web_tac.git
   cd dcs_web_tac
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic python-multipart
   ```

## Running the Application
1. Initialize the database (first time only):
   ```bash
   python src/db_init.py
   ```
2. Start the server:
   ```bash
   python -m uvicorn src.main:app --reload
   ```
3. Open your browser and navigate to:
   [http://localhost:8000](http://localhost:8000)

## Features to try
- **Upload**: Drag and drop your `.acmi` files to the "Upload" button (mock UI logic).
- **View**: Select a mission from the sidebar to see the 3D trajectory in Cesium.
- **HUD**: Watch the top-right telemetry update as the timeline moves.
