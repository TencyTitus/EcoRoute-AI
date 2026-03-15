from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.common import CoordinateSchema, TimeWindowSchema, RouteMetrics, EmissionComparison, RouteConditionsSchema

class DeliveryPointCreate(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    demand: float = Field(default=0.0, ge=0)
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    service_time: int = Field(default=300, ge=0)  # seconds
    priority: int = Field(default=1, ge=1, le=3)
    notes: Optional[str] = None

class DeliveryPointResponse(BaseModel):
    id: int
    name: str
    address: Optional[str]
    latitude: float
    longitude: float
    demand: float
    time_window_start: Optional[datetime]
    time_window_end: Optional[datetime]
    service_time: int
    priority: int
    notes: Optional[str]
    
    class Config:
        orm_mode = True

class RouteOptimizationRequest(BaseModel):
    vehicle_id: int
    delivery_points: List[int]  # List of delivery point IDs
    start_location: CoordinateSchema
    end_location: Optional[CoordinateSchema] = None  # If None, return to start
    optimization_objective: str = Field(default="balanced", pattern="^(time|emission|balanced)$")
    max_route_duration_minutes: Optional[int] = Field(default=480, ge=0)  # 8 hours default
    include_traffic: bool = True
    include_weather: bool = True

class RouteSegment(BaseModel):
    from_point: str
    to_point: str
    distance_km: float
    duration_minutes: float
    co2_kg: float
    coordinates: List[List[float]]  # [[lon, lat], [lon, lat], ...]

class OptimizedRouteResponse(BaseModel):
    id: int
    name: str
    route_type: str
    vehicle_id: int
    total_distance_km: float
    total_duration_minutes: float
    estimated_co2_kg: float
    estimated_fuel_liters: float
    optimization_objective: str
    delivery_sequence: List[int]  # Ordered list of delivery point IDs
    route_segments: List[RouteSegment]
    conditions: Optional[RouteConditionsSchema] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class RouteComparisonResponse(BaseModel):
    fastest_route: OptimizedRouteResponse
    eco_friendly_route: OptimizedRouteResponse
    comparison: EmissionComparison
    pareto_optimal: bool
    recommendation: str  # Text recommendation based on trade-offs

class BulkDeliveryPointUpload(BaseModel):
    points: List[DeliveryPointCreate]

class DirectRouteRequest(BaseModel):
    start_location: CoordinateSchema
    end_location: CoordinateSchema
    transport_type: str = Field(default="car", pattern="^(car|van|truck|ev)$")
    optimization_objective: str = Field(default="balanced", pattern="^(time|emission|balanced)$")

class RouteAssignmentRequest(BaseModel):
    route_data: OptimizedRouteResponse
    driver_id: int
