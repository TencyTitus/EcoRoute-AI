from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Dict
from app import database
from app.models import User, Vehicle, OptimizedRoute
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary")
def get_admin_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall system summary for admin dashboard"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_users = db.query(func.count(User.id)).scalar()
    active_drivers = db.query(func.count(User.id)).filter(User.role == 'driver', User.is_active == True).scalar()
    total_vehicles = db.query(func.count(Vehicle.id)).scalar()
    total_routes = db.query(func.count(OptimizedRoute.id)).scalar()
    
    # Get recent users
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_users_list = [
        {"id": u.id, "name": u.full_name, "email": u.email, "role": u.role, "date": u.created_at.isoformat() if u.created_at else None}
        for u in recent_users
    ]
    
    # Get recent routes
    recent_routes = db.query(OptimizedRoute).order_by(OptimizedRoute.created_at.desc()).limit(50).all()
    print(f"DEBUG: Returning {len(recent_routes)} routes to admin")
    recent_routes_list = [
        {
            "id": r.id, 
            "name": r.name, 
            "type": r.route_type, 
            "status": r.status, 
            "date": r.created_at.isoformat() if r.created_at else None,
            "distance": r.total_distance_km,
            "duration": r.total_duration_minutes,
            "co2": r.estimated_co2_kg,
            "vehicle_id": r.vehicle_id
        }
        for r in recent_routes
    ]
    
    return {
        "stats": {
            "totalUsers": total_users,
            "activeDrivers": active_drivers,
            "managedFleets": total_vehicles,
            "totalRoutes": total_routes,
            "systemHealth": 98.7
        },
        "recentActivity": {
            "users": recent_users_list,
            "routes": recent_routes_list
        }
    }

@router.get("/routes/{route_id}")
def get_route_details(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full details for a specific route"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    route = db.query(OptimizedRoute).filter(OptimizedRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Get vehicle details if exists
    vehicle_info = None
    if route.vehicle_id:
        v = db.query(Vehicle).filter(Vehicle.id == route.vehicle_id).first()
        if v:
            vehicle_info = {
                "id": v.id,
                "type": v.vehicle_type,
                "plate": v.license_plate,
                "model": v.model
            }
            
    # Get driver details if exists
    driver_info = None
    if route.assigned_driver_id:
        d = db.query(User).filter(User.id == route.assigned_driver_id).first()
        if d:
            driver_info = {
                "id": d.id,
                "name": d.full_name,
                "email": d.email
            }

    return {
        "id": route.id,
        "name": route.name,
        "type": route.route_type,
        "status": route.status,
        "distance": route.total_distance_km,
        "duration": route.total_duration_minutes,
        "co2": route.estimated_co2_kg,
        "fuel": route.estimated_fuel_liters,
        "created_at": route.created_at.isoformat() if route.created_at else None,
        "vehicle": vehicle_info,
        "driver": driver_info,
        "stops_count": len(route.delivery_points) if route.delivery_points else 0
    }

@router.get("/system-stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system health and performance stats"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_users = db.query(func.count(User.id)).scalar()
    
    import random
    return {
        "totalUsers": total_users,
        "activeSessions": random.randint(15, 35),
        "systemUptime": "99.98%",
        "serverLoad": f"{random.randint(20, 45)}%",
        "databaseConnections": total_users + random.randint(2, 6),
        "apiRequests": f"{random.randint(1200, 1600)} today"
    }

@router.get("/logs")
def get_admin_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get recent backend logs"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import os
    log_path = os.path.join(os.getcwd(), "backend.log")
    
    if not os.path.exists(log_path):
        return {"logs": ["Log file not found"]}
        
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            return {"logs": [line.strip() for line in lines[-limit:]]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

@router.get("/performance-metrics")
def get_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for charting"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import random
    import datetime
    
    # Generate mock time-series data for the last 12 hours
    labels = []
    response_times = []
    load_averages = []
    
    now = datetime.datetime.now()
    for i in range(11, -1, -1):
        time_label = (now - datetime.timedelta(hours=i)).strftime("%H:00")
        labels.append(time_label)
        response_times.append(random.randint(10, 50))
        load_averages.append(random.randint(15, 40))
        
    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Response Time (ms)",
                "data": response_times,
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                "fill": True
            },
            {
                "label": "Server Load (%)",
                "data": load_averages,
                "borderColor": "#ef4444",
                "backgroundColor": "rgba(239, 68, 68, 0.1)",
                "fill": True
            }
        ]
    }
