from fastapi import FastAPI
import sqlite3

app = FastAPI(title="DCS Web-Tac API")

@app.get("/")
def read_root():
    return {"status": "DCS Web-Tac is running"}

@app.get("/sorties")
def get_sorties():
    # Placeholder for database retrieval
    return []
