from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from . import schemas, database, parser, db_init, logger

# Use the structured logger
app_logger = logger.logger

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    app_logger.info("System starting up...")
    os.makedirs("data/uploads", exist_ok=True)
    db_init.init_db()
    try:
        with database.get_db() as db:
            cursor = db.cursor()
            # Ensure table exists (init_db does it, but double check is harmless)
            try:
                count = cursor.execute("SELECT count(*) FROM sorties").fetchone()[0]
                if count == 0:
                    sample_path = os.path.join("data", "samples", "full_flight_sim.acmi")
                    if os.path.exists(sample_path):
                        app_logger.info(f"Loading default sample from {sample_path}")
                        acmi_parser = parser.AcmiParser()
                        acmi_parser.parse_file(sample_path)
            except Exception as inner_e:
                app_logger.warning(f"DB check skipped: {inner_e}")
    except Exception as e:
        app_logger.error(f"Startup DB Error: {e}")
    
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title="DCS Web-Tac API",
    description="Professional flight data analysis backend for DCS World.",
    version="0.2.3",
    lifespan=lifespan
)

# Initialize database on startup removed (migrated to lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/api/", tags=["Health"])
def read_root():
    return {"status": "DCS Web-Tac Online", "version": "0.2.2"}

@app.get("/api/sorties", response_model=List[schemas.Sortie], tags=["Data"])
def list_sorties():
    with database.get_db() as db:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM sorties ORDER BY start_time DESC").fetchall()
        return [dict(row) for row in rows]

@app.get("/api/sorties/{sortie_id}/objects", response_model=List[schemas.Object], tags=["Data"])
def list_objects(sortie_id: int):
    with database.get_db() as db:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM objects WHERE sortie_id = ? ORDER BY name", (sortie_id,)).fetchall()
        return [dict(row) for row in rows]

@app.get("/api/sorties/{sortie_id}/telemetry", response_model=List[schemas.TelemetryBase], tags=["Data"])
def get_telemetry(sortie_id: int, obj_id: str | None = None):
    with database.get_db() as db:
        cursor = db.cursor()
        if obj_id:
            rows = cursor.execute(
                "SELECT * FROM telemetry WHERE sortie_id = ? AND obj_id = ? ORDER BY time_offset",
                (sortie_id, obj_id)
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM telemetry WHERE sortie_id = ? ORDER BY time_offset",
                (sortie_id,)
            ).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Sortie data not found")
        return [dict(row) for row in rows]

@app.post("/api/upload", tags=["Ingestion"])
async def upload_acmi(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not (file.filename.endswith(".acmi") or file.filename.endswith(".zip") or file.filename.endswith(".gz")):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    file_path = os.path.join("data/uploads", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_acmi, file_path)
    return {"message": f"Successfully uploaded {file.filename}"}

def process_acmi(file_path: str):
    acmi_parser = parser.AcmiParser()
    acmi_parser.parse_file(file_path)

# Mount static files using absolute paths to be environment-agnostic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "static"))

if os.path.exists(STATIC_DIR):
    app_logger.info(f"Mounting static files from {STATIC_DIR}")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    app_logger.error(f"Static directory NOT FOUND at {STATIC_DIR}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
