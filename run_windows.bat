@echo off
echo Starting DCS Web-Tac...
pip install fastapi uvicorn pydantic python-multipart
python src/db_init.py
echo Open your browser at http://localhost:8000
python -m uvicorn src.main:app --reload
pause
