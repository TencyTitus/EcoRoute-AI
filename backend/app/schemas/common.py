from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CoordinateSchema(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class TimeWindowSchema(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None

class RouteMetrics(BaseModel):
    total_distance_km: float
    total_duration_minutes: float
    estimated_co2_kg: float
    estimated_fuel_liters: float
    number_of_stops: int
    avg_speed_kmh: float

class EmissionComparison(BaseModel):
    fastest_route_co2_kg: float
    eco_route_co2_kg: float
    co2_savings_kg: float
    co2_savings_percent: float
    
    fastest_route_time_min: float
    eco_route_time_min: float
    time_difference_min: float
    time_difference_percent: float

class WeatherConditions(BaseModel):
    condition: str
    temperature_celsius: float
    humidity_percent: int
    wind_speed_kmh: float
    precipitation_mm: float

class RouteConditionsSchema(BaseModel):
    avg_traffic_speed_kmh: float
    weather: WeatherConditions
    weather_impact_factor: float
    traffic_impact_factor: float
