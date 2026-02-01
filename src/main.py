from fastapi import FastAPI, Depends, HTTPException
from typing import List
from . import schemas, database

app = FastAPI(
    title="DCS Web-Tac API",
    description="Professional flight data analysis backend for DCS World.",
    version="0.1.0"
)

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
