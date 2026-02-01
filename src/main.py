from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import List
import os
import shutil
from . import schemas, database, parser

app = FastAPI(
    title="DCS Web-Tac API",
    description="Professional flight data analysis backend for DCS World.",
    version="0.1.1"
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", tags=["Health"])
def read_root():
    return {"status": "DCS Web-Tac System Online", "principles_adhered": True}

@app.get("/sorties", response_model=List[schemas.Sortie], tags=["Data"])
def list_sorties():
    with database.get_db() as db:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM sorties ORDER BY start_time DESC").fetchall()
        return [dict(row) for row in rows]

@app.get("/sorties/{sortie_id}/telemetry", response_model=List[schemas.TelemetryBase], tags=["Data"])
def get_telemetry(sortie_id: int):
    with database.get_db() as db:
        cursor = db.cursor()
        rows = cursor.execute("SELECT * FROM telemetry WHERE sortie_id = ? ORDER BY time_offset", (sortie_id,)).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Sortie data not found")
        return [dict(row) for row in rows]

@app.post("/upload", tags=["Ingestion"])
async def upload_acmi(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a .acmi, .zip, or .gz file for processing.
    The processing runs in the background to keep the UI responsive.
    """
    if not (file.filename.endswith(".acmi") or file.filename.endswith(".zip") or file.filename.endswith(".gz")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .acmi, .zip, or .gz")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Start background parsing
    background_tasks.add_task(process_acmi, file_path)

    return {"message": f"Successfully uploaded {file.filename}. Processing in background.", "filename": file.filename}

def process_acmi(file_path: str):
    acmi_parser = parser.AcmiParser()
    acmi_parser.parse_file(file_path)
