from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.database import Base

class DeliveryPoint(Base):
    __tablename__ = "delivery_points"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT', srid=4326))
    
    # Delivery requirements
    demand = Column(Float, default=0.0)  # in kg or units
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    service_time = Column(Integer, default=300)  # in seconds
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    notes = Column(String(1000))
    
    # Relationships
    routes = relationship("OptimizedRoute", secondary="route_delivery_points", back_populates="delivery_points")
