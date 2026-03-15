from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime, timedelta
from app import database
from app.models import OptimizedRoute, RouteHistory, User, Vehicle
from app.routers.auth import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/fleet-performance")
def get_fleet_performance(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fleet performance metrics for the specified period"""
    
    since_date = datetime.now() - timedelta(days=days)
    
    # Base filters
    route_filter = OptimizedRoute.created_at >= since_date
    vehicle_filter = Vehicle.status == 'available'
    
    if current_user.role == "manager":
        route_filter = (route_filter) & (OptimizedRoute.created_by_id == current_user.id)
        vehicle_filter = (vehicle_filter) & (Vehicle.created_by_id == current_user.id)
    
    # Total routes
    total_routes = db.query(func.count(OptimizedRoute.id)).filter(route_filter).scalar()
    
    # Total distance
    total_distance = db.query(func.sum(OptimizedRoute.total_distance_km)).filter(route_filter).scalar() or 0
    
    # Total emissions
    total_emissions = db.query(func.sum(OptimizedRoute.estimated_co2_kg)).filter(route_filter).scalar() or 0
    
    # Total fuel
    total_fuel = db.query(func.sum(OptimizedRoute.estimated_fuel_liters)).filter(route_filter).scalar() or 0
    
    # Average metrics
    avg_distance = total_distance / total_routes if total_routes > 0 else 0
    avg_emissions = total_emissions / total_routes if total_routes > 0 else 0
    
    # Active vehicles
    active_vehicles = db.query(func.count(Vehicle.id)).filter(vehicle_filter).scalar()
    
    return {
        "period_days": days,
        "total_routes": total_routes,
        "total_distance_km": round(total_distance, 2),
        "total_emissions_kg": round(total_emissions, 2),
        "total_fuel_liters": round(total_fuel, 2),
        "avg_distance_per_route_km": round(avg_distance, 2),
        "avg_emissions_per_route_kg": round(avg_emissions, 2),
        "active_vehicles": active_vehicles,
        "efficiency_score": round(min(100, (1000 / (avg_emissions + 1)) * 10), 2)
    }

@router.get("/emission-trends")
def get_emission_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily emission trends"""
    
    since_date = datetime.now() - timedelta(days=days)
    
    # Query routes grouped by date
    routes = db.query(
        func.date(OptimizedRoute.created_at).label('date'),
        func.sum(OptimizedRoute.estimated_co2_kg).label('total_co2'),
        func.sum(OptimizedRoute.total_distance_km).label('total_distance'),
        func.count(OptimizedRoute.id).label('route_count')
    ).filter(
        OptimizedRoute.created_at >= since_date
    ).group_by(
        func.date(OptimizedRoute.created_at)
    ).order_by('date').all()
    
    trends = []
    for route in routes:
        trends.append({
            "date": route.date.isoformat(),
            "total_co2_kg": round(route.total_co2, 2),
            "total_distance_km": round(route.total_distance, 2),
            "route_count": route.route_count,
            "avg_co2_per_km": round(route.total_co2 / route.total_distance, 3) if route.total_distance > 0 else 0
        })
    
    return {
        "period_days": days,
        "trends": trends
    }

@router.get("/route-comparison-stats")
def get_route_comparison_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics on route type usage and savings"""
    
    since_date = datetime.now() - timedelta(days=days)
    
    # Count by route type
    fastest_count = db.query(func.count(OptimizedRoute.id)).filter(
        OptimizedRoute.route_type == 'fastest',
        OptimizedRoute.created_at >= since_date
    ).scalar()
    
    eco_count = db.query(func.count(OptimizedRoute.id)).filter(
        OptimizedRoute.route_type == 'eco_friendly',
        OptimizedRoute.created_at >= since_date
    ).scalar()
    
    # Emissions by type
    fastest_emissions = db.query(func.sum(OptimizedRoute.estimated_co2_kg)).filter(
        OptimizedRoute.route_type == 'fastest',
        OptimizedRoute.created_at >= since_date
    ).scalar() or 0
    
    eco_emissions = db.query(func.sum(OptimizedRoute.estimated_co2_kg)).filter(
        OptimizedRoute.route_type == 'eco_friendly',
        OptimizedRoute.created_at >= since_date
    ).scalar() or 0
    
    # Calculate potential savings if all routes were eco-friendly
    avg_fastest_emission = fastest_emissions / fastest_count if fastest_count > 0 else 0
    potential_savings = (avg_fastest_emission - (eco_emissions / eco_count if eco_count > 0 else 0)) * (fastest_count + eco_count)
    
    return {
        "period_days": days,
        "fastest_route_count": fastest_count,
        "eco_route_count": eco_count,
        "eco_adoption_rate": round((eco_count / (fastest_count + eco_count) * 100) if (fastest_count + eco_count) > 0 else 0, 2),
        "fastest_total_emissions_kg": round(fastest_emissions, 2),
        "eco_total_emissions_kg": round(eco_emissions, 2),
        "potential_savings_kg": round(max(0, potential_savings), 2)
    }

@router.get("/vehicle-efficiency")
def get_vehicle_efficiency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get efficiency metrics for each vehicle"""
    
    # Query routes grouped by vehicle
    vehicle_stats = db.query(
        Vehicle.id,
        Vehicle.license_plate,
        Vehicle.vehicle_type,
        func.count(OptimizedRoute.id).label('route_count'),
        func.sum(OptimizedRoute.total_distance_km).label('total_distance'),
        func.sum(OptimizedRoute.estimated_co2_kg).label('total_co2'),
        func.sum(OptimizedRoute.estimated_fuel_liters).label('total_fuel')
    ).join(
        OptimizedRoute, Vehicle.id == OptimizedRoute.vehicle_id
    ).group_by(
        Vehicle.id, Vehicle.license_plate, Vehicle.vehicle_type
    ).all()
    
    vehicles = []
    for stat in vehicle_stats:
        vehicles.append({
            "vehicle_id": stat.id,
            "license_plate": stat.license_plate,
            "vehicle_type": stat.vehicle_type,
            "route_count": stat.route_count,
            "total_distance_km": round(stat.total_distance, 2),
            "total_co2_kg": round(stat.total_co2, 2),
            "total_fuel_liters": round(stat.total_fuel, 2),
            "avg_co2_per_km": round(stat.total_co2 / stat.total_distance, 3) if stat.total_distance > 0 else 0,
            "avg_fuel_per_km": round(stat.total_fuel / stat.total_distance, 3) if stat.total_distance > 0 else 0
        })
    
    return {
        "vehicles": vehicles,
        "total_vehicles": len(vehicles)
    }

@router.get("/cost-savings")
def get_cost_savings(
    days: int = 30,
    fuel_cost_per_liter: float = 1.5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate cost savings from eco-friendly routes"""
    
    since_date = datetime.now() - timedelta(days=days)
    
    # Get eco-friendly routes
    eco_routes = db.query(OptimizedRoute).filter(
        OptimizedRoute.route_type == 'eco_friendly',
        OptimizedRoute.created_at >= since_date
    ).all()
    
    total_fuel_saved = 0
    total_co2_saved = 0
    
    # Estimate savings (assume 10% average savings for eco routes)
    for route in eco_routes:
        estimated_savings = route.estimated_fuel_liters * 0.10
        total_fuel_saved += estimated_savings
        total_co2_saved += estimated_savings * 2.68  # kg CO2 per liter
    
    cost_savings = total_fuel_saved * fuel_cost_per_liter
    
    return {
        "period_days": days,
        "fuel_cost_per_liter": fuel_cost_per_liter,
        "total_fuel_saved_liters": round(total_fuel_saved, 2),
        "total_co2_saved_kg": round(total_co2_saved, 2),
        "cost_savings": round(cost_savings, 2),
        "eco_routes_count": len(eco_routes)
    }
