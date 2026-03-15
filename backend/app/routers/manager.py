from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from app import database
from app.models import User, Vehicle, OptimizedRoute, DeliveryPoint, route_delivery_points
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/my-routes")
def get_manager_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all routes created by this manager"""
    if current_user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    routes = db.query(OptimizedRoute).filter(
        OptimizedRoute.created_by_id == current_user.id
    ).order_by(OptimizedRoute.created_at.desc()).all()
    
    serialized_routes = []
    for route in routes:
        vehicle = db.query(Vehicle).filter(Vehicle.id == route.vehicle_id).first()
        driver = db.query(User).filter(User.id == route.assigned_driver_id).first()
        
        serialized_routes.append({
            "id": route.id,
            "name": route.name,
            "type": route.route_type,
            "status": route.status,
            "distance": route.total_distance_km,
            "duration": route.total_duration_minutes,
            "co2": route.estimated_co2_kg,
            "created_at": route.created_at,
            "vehicle": {
                "id": vehicle.id,
                "plate": vehicle.license_plate,
                "type": vehicle.vehicle_type
            } if vehicle else None,
            "driver": {
                "id": driver.id,
                "name": driver.full_name
            } if driver else None
        })
        
    return serialized_routes

@router.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a route created by this manager"""
    route = db.query(OptimizedRoute).filter(OptimizedRoute.id == route_id).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Security: Only owner or admin can delete
    if route.created_by_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this route")
        
    # Delete associations first
    from app.models import RouteHistory
    db.query(RouteHistory).filter(RouteHistory.route_id == route_id).delete()
    db.execute(route_delivery_points.delete().where(route_delivery_points.c.route_id == route_id))
    
    db.delete(route)
    db.commit()
    
    return {"message": "Route deleted successfully"}

@router.patch("/routes/{route_id}/rename")
def rename_route(
    route_id: int,
    name: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rename a route created by this manager"""
    route = db.query(OptimizedRoute).filter(OptimizedRoute.id == route_id).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    if route.created_by_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this route")
        
    route.name = name
    db.commit()
    
    return {"message": "Route renamed successfully", "name": route.name}
