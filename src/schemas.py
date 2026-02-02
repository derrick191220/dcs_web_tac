from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TelemetryBase(BaseModel):
    obj_id: Optional[str] = None
    time_offset: float
    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None
    roll: Optional[float] = 0.0
    pitch: Optional[float] = 0.0
    yaw: Optional[float] = 0.0
    u: Optional[float] = None
    v: Optional[float] = None
    heading: Optional[float] = None
    ias: Optional[float] = None
    mach: Optional[float] = 0.0
    g_force: Optional[float] = None
    fuel_remaining: Optional[float] = 0.0
    raw: Optional[str] = None

class SortieBase(BaseModel):
    mission_name: str
    pilot_name: str
    aircraft_type: str
    start_time: datetime
    map_name: Optional[str] = None
    parse_status: Optional[str] = None
    reference_time: Optional[str] = None

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
    raw: Optional[str] = None
    callsign: Optional[str] = None
    color: Optional[str] = None
    shape: Optional[str] = None
    model_config = {"from_attributes": True}

class Event(BaseModel):
    id: int
    sortie_id: int
    time_offset: float
    event_type: str
    object_ids: Optional[str] = None
    text: Optional[str] = None
    raw: Optional[str] = None
    model_config = {"from_attributes": True}

class ParseJob(BaseModel):
    id: str
    sortie_id: Optional[int] = None
    file_name: Optional[str] = None
    status: str
    progress_pct: Optional[float] = 0.0
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
