from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Vehicle Schemas
class VehicleCreate(BaseModel):
    vehicle_type: str
    license_plate: str
    model: Optional[str] = None
    year: Optional[int] = None
    fuel_type: str
    emission_factor: float
    fuel_efficiency_kmpl: float
    engine_size: float = 2.0
    cylinders: int = 4
    max_capacity_kg: float
    max_volume_m3: Optional[float] = None
    avg_speed_kmh: float = 50.0
    cost_per_km: Optional[float] = None

class Vehicle(BaseModel):
    id: int
    vehicle_type: str
    license_plate: str
    model: Optional[str]
    year: Optional[int]
    fuel_type: str
    emission_factor: float
    fuel_efficiency_kmpl: float
    engine_size: float
    cylinders: int
    max_capacity_kg: float
    max_volume_m3: Optional[float]
    avg_speed_kmh: float
    status: str
    cost_per_km: Optional[float]
    created_by_id: Optional[int] = None

    class Config:
        orm_mode = True

# Route Schemas (for legacy routes.py)
class RouteCreate(BaseModel):
    source: str
    destination: str
    distance_km: float

class Route(BaseModel):
    id: int
    source: str
    destination: str
    distance_km: float

    class Config:
        orm_mode = True

# Emission Log Schemas
class EmissionLogCreate(BaseModel):
    vehicle_id: int
    route_id: int
    co2_emission: float

class EmissionLog(BaseModel):
    id: int
    vehicle_id: int
    route_id: int
    co2_emission: float
    recorded_at: datetime

    class Config:
        orm_mode = True

# Import user schemas
from .user import UserCreate, UserLogin, UserResponse
