from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from . import schemas, database, parser, db_init

app = FastAPI(
    title="DCS Web-Tac API",
    description="Professional flight data analysis backend for DCS World.",
    version="0.2.1"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    db_init.init_db()
    # Pre-load the sample data if DB is empty
    try:
        with database.get_db() as db:
            count = db.cursor().execute("SELECT count(*) FROM sorties").fetchone()[0]
            if count == 0:
                sample_path = os.path.join(os.path.dirname(__file__), "data", "samples", "full_flight_sim.acmi")
                # Fallback for relative path
                if not os.path.exists(sample_path):
                    sample_path = "data/samples/full_flight_sim.acmi"
                
                if os.path.exists(sample_path):
                    acmi_parser = parser.AcmiParser()
                    acmi_parser.parse_file(sample_path)
    except Exception as e:
        print(f"Startup DB Error: {e}")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# API Endpoints
@app.get("/api/", tags=["Health"])
def read_root():
    return {"status": "DCS Web-Tac System Online", "version": "0.2.1", "principles_adhered": True}

@app.get("/api/sorties", response_model=List[schemas.Sortie], tags=["Data"])
def list_sorties():
    with database.get_db() as db:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM sorties ORDER BY start_time DESC").fetchall()
        return [dict(row) for row in rows]

@app.get("/api/sorties/{sortie_id}/telemetry", response_model=List[schemas.TelemetryBase], tags=["Data"])
def get_telemetry(sortie_id: int):
    with database.get_db() as db:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM telemetry WHERE sortie_id = ? ORDER BY time_offset", (sortie_id,)).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Sortie data not found")
        return [dict(row) for row in rows]

@app.post("/api/upload", tags=["Ingestion"])
async def upload_acmi(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not (file.filename.endswith(".acmi") or file.filename.endswith(".zip") or file.filename.endswith(".gz")):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_acmi, file_path)
    return {"message": f"Successfully uploaded {file.filename}", "filename": file.filename}

def process_acmi(file_path: str):
    acmi_parser = parser.AcmiParser()
    acmi_parser.parse_file(file_path)

# Serve Frontend Static Files
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if not os.path.exists(static_path):
    static_path = "static"
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
