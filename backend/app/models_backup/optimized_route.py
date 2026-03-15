from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base

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
