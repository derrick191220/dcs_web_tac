from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TelemetryBase(BaseModel):
    obj_id: Optional[str] = None
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
    model_config = {"from_attributes": True}

class ObjectBase(BaseModel):
    obj_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    coalition: Optional[str] = None
    pilot: Optional[str] = None

class Object(ObjectBase):
    id: int
    sortie_id: int
    model_config = {"from_attributes": True}
