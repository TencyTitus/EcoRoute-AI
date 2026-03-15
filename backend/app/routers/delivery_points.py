from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import database
from app.schemas.optimization import DeliveryPointCreate, DeliveryPointResponse, BulkDeliveryPointUpload
from app.models import DeliveryPoint, User
from app.services.geospatial_utils import create_point_wkt
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/delivery-points",
    tags=["Delivery Points"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=DeliveryPointResponse)
def create_delivery_point(
    point: DeliveryPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new delivery point"""
    
    # Create WKT point for PostGIS
    point_wkt = create_point_wkt(point.latitude, point.longitude)
    
    db_point = DeliveryPoint(
        name=point.name,
        address=point.address,
        latitude=point.latitude,
        longitude=point.longitude,
        location=point_wkt,
        demand=point.demand,
        time_window_start=point.time_window_start,
        time_window_end=point.time_window_end,
        service_time=point.service_time,
        priority=point.priority,
        notes=point.notes,
        created_by=current_user.id
    )
    
    db.add(db_point)
    db.commit()
    db.refresh(db_point)
    
    return db_point

@router.post("/bulk", response_model=List[DeliveryPointResponse])
def create_bulk_delivery_points(
    upload: BulkDeliveryPointUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create multiple delivery points at once"""
    
    created_points = []
    
    for point in upload.points:
        point_wkt = create_point_wkt(point.latitude, point.longitude)
        
        db_point = DeliveryPoint(
            name=point.name,
            address=point.address,
            latitude=point.latitude,
            longitude=point.longitude,
            location=point_wkt,
            demand=point.demand,
            time_window_start=point.time_window_start,
            time_window_end=point.time_window_end,
            service_time=point.service_time,
            priority=point.priority,
            notes=point.notes,
            created_by=current_user.id
        )
        
        db.add(db_point)
        created_points.append(db_point)
    
    db.commit()
    
    for point in created_points:
        db.refresh(point)
    
    return created_points

@router.get("/", response_model=List[DeliveryPointResponse])
def get_delivery_points(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all delivery points"""
    
    points = db.query(DeliveryPoint).offset(skip).limit(limit).all()
    return points

@router.get("/{point_id}", response_model=DeliveryPointResponse)
def get_delivery_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific delivery point"""
    
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    
    if not point:
        raise HTTPException(status_code=404, detail="Delivery point not found")
    
    return point

@router.delete("/{point_id}")
def delete_delivery_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a delivery point"""
    
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    
    if not point:
        raise HTTPException(status_code=404, detail="Delivery point not found")
    
    db.delete(point)
    db.commit()
    
    return {"message": "Delivery point deleted successfully"}
