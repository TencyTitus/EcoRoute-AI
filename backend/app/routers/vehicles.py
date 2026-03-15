from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import database, models, schemas

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.routers.auth import get_current_user

# Create a new vehicle
@router.post("/", response_model=schemas.Vehicle)
def create_vehicle(
    vehicle: schemas.VehicleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_vehicle = models.Vehicle(**vehicle.dict())
    db_vehicle.created_by_id = current_user.id
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


# Get all vehicles
@router.get("/", response_model=List[schemas.Vehicle])
def read_vehicles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Vehicle)
    
    # Managers only see their own vehicles
    if current_user.role == "manager":
        query = query.filter(models.Vehicle.created_by_id == current_user.id)
        
    vehicles = query.offset(skip).limit(limit).all()
    return vehicles
