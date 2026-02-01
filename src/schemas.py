from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TelemetryBase(BaseModel):
    time_offset: float
    lat: float
    lon: float
    alt: float
    roll: Optional[float] = 0.0
    pitch: Optional[float] = 0.0
    yaw: Optional[float] = 0.0
    ias: float
    mach: Optional[float] = 0.0
    g_force: float
    fuel_remaining: Optional[float] = 0.0

class SortieBase(BaseModel):
    mission_name: str
    pilot_name: str
    aircraft_type: str
    start_time: datetime
    map_name: Optional[str] = None

class Sortie(SortieBase):
    id: int

    class Config:
        from_attributes = True
