from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, Boolean, DateTime, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base

# ============================================================================
# LEGACY MODELS (from original models.py)
# ============================================================================

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    vehicle_type = Column(String(50))  # truck, van, car
    license_plate = Column(String(50), unique=True)
    model = Column(String(100))
    year = Column(Integer)
    
    # Fuel and emissions
    fuel_type = Column(String(20))  # diesel, petrol, electric, hybrid
    emission_factor = Column(Float)  # kg CO2 per liter
    fuel_efficiency_kmpl = Column(Float)  # km per liter
    engine_size = Column(Float, default=2.0)  # L
    cylinders = Column(Integer, default=4)
    
    # Capacity and operational parameters
    max_capacity_kg = Column(Float)
    max_volume_m3 = Column(Float)
    avg_speed_kmh = Column(Float, default=50.0)
    status = Column(String(20), default='available')  # available, in_use, maintenance
    cost_per_km = Column(Float)
    
    # Relationships
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    optimized_routes = relationship("OptimizedRoute", back_populates="vehicle")

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(200))
    destination = Column(String(200))
    distance_km = Column(Float)
    route_geom = Column(Geometry('LINESTRING'))

class EmissionLog(Base):
    __tablename__ = "emission_logs"
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    co2_emission = Column(Float)
    recorded_at = Column(TIMESTAMP, server_default=func.now())

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(200))
    email = Column(String(200), unique=True, index=True)
    password_hash = Column(String(200))
    role = Column(String(50))  # admin, manager, driver
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

# ============================================================================
# DELIVERY POINT MODEL
# ============================================================================

class DeliveryPoint(Base):
    __tablename__ = "delivery_points"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    address = Column(String(500))
    
    # Geospatial data
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(Geometry('POINT', srid=4326))
    
    # Delivery requirements
    demand = Column(Float, default=0)  # kg or units
    time_window_start = Column(DateTime(timezone=True), nullable=True)
    time_window_end = Column(DateTime(timezone=True), nullable=True)
    service_time = Column(Integer, default=300)  # seconds
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    notes = Column(String(1000), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    routes = relationship("OptimizedRoute", secondary="route_delivery_points", back_populates="delivery_points")

# ============================================================================
# OPTIMIZED ROUTE MODELS
# ============================================================================

# Association table for many-to-many relationship
route_delivery_points = Table(
    'route_delivery_points',
    Base.metadata,
    Column('route_id', Integer, ForeignKey('optimized_routes.id'), primary_key=True),
    Column('delivery_point_id', Integer, ForeignKey('delivery_points.id'), primary_key=True),
    Column('sequence_order', Integer)  # Order in which points are visited
)

class OptimizedRoute(Base):
    __tablename__ = "optimized_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    route_type = Column(String(50))  # 'fastest', 'eco_friendly', 'balanced'
    
    # Vehicle assignment
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    vehicle = relationship("Vehicle", back_populates="optimized_routes")
    
    # Route geometry and metrics
    route_geometry = Column(Geometry('LINESTRING', srid=4326))
    total_distance_km = Column(Float)
    total_duration_minutes = Column(Float)
    
    # Emission metrics
    estimated_co2_kg = Column(Float)
    estimated_fuel_liters = Column(Float)
    
    # Optimization metadata
    optimization_objective = Column(String(50))  # 'time', 'emission', 'balanced'
    constraints_applied = Column(JSON)  # Store constraints as JSON
    
    # Comparison data (for Pareto analysis)
    pareto_rank = Column(Integer)  # 1 = on Pareto front
    time_vs_baseline_percent = Column(Float)
    emission_vs_baseline_percent = Column(Float)
    
    # Status and tracking
    status = Column(String(50), default='planned')  # planned, active, completed, cancelled
    assigned_driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    delivery_points = relationship("DeliveryPoint", secondary=route_delivery_points, back_populates="routes")
    route_history = relationship("RouteHistory", back_populates="route")

class RouteHistory(Base):
    """TimescaleDB hypertable for time-series route performance data"""
    __tablename__ = "route_history"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("optimized_routes.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Actual performance metrics
    actual_distance_km = Column(Float)
    actual_duration_minutes = Column(Float)
    actual_fuel_consumed_liters = Column(Float, nullable=True)
    actual_co2_kg = Column(Float, nullable=True)
    
    # Prediction accuracy
    distance_error_percent = Column(Float)
    duration_error_percent = Column(Float)
    fuel_error_percent = Column(Float, nullable=True)
    
    # Environmental conditions during execution
    avg_traffic_speed_kmh = Column(Float)
    weather_condition = Column(String(50))
    temperature_celsius = Column(Float)
    
    # Driver feedback
    driver_rating = Column(Integer)  # 1-5
    driver_notes = Column(String(1000))
    
    # Relationship
    route = relationship("OptimizedRoute", back_populates="route_history")
