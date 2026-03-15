from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app import database
from app.schemas.optimization import (
    RouteOptimizationRequest,
    OptimizedRouteResponse,
    RouteComparisonResponse, 
    RouteSegment,
    DirectRouteRequest,
    RouteAssignmentRequest
)
from app.models import User, DeliveryPoint, OptimizedRoute, route_delivery_points, Vehicle
from app.routers.auth import get_current_user
from app.services.route_optimizer import RouteOptimizer
from app.services.geospatial_utils import create_linestring, interpolate_route_points

router = APIRouter(
    prefix="/optimization",
    tags=["Route Optimization"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/optimize", response_model=RouteComparisonResponse)
def optimize_route(
    request: RouteOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate optimized routes using multi-objective optimization
    Returns both fastest and eco-friendly routes for comparison
    """
    
    # Get vehicle data
    vehicle = db.query(Vehicle).filter(Vehicle.id == request.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    # Verify vehicle ownership for managers
    if current_user.role == "manager" and vehicle.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to use this vehicle")
    
    # Get delivery points
    delivery_points = db.query(DeliveryPoint).filter(
        DeliveryPoint.id.in_(request.delivery_points)
    ).all()
    
    if len(delivery_points) != len(request.delivery_points):
        raise HTTPException(status_code=404, detail="One or more delivery points not found")
    
    # Prepare data for optimizer
    start_location = (request.start_location.latitude, request.start_location.longitude)
    delivery_locations = [(dp.latitude, dp.longitude) for dp in delivery_points]
    
    vehicle_data = {
        'avg_speed_kmh': vehicle.avg_speed_kmh or 50.0,
        'fuel_efficiency_kmpl': vehicle.fuel_efficiency_kmpl or 10.0,
        'emission_factor': vehicle.emission_factor or 2.68,
        'max_capacity_kg': vehicle.max_capacity_kg or 1000.0
    }
    
    # Run optimization
    optimizer = RouteOptimizer()
    result = optimizer.generate_pareto_solutions(
        start_location,
        delivery_locations,
        vehicle_data,
        max_duration_seconds=(request.max_route_duration_minutes or 480) * 60
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Build responses (mocking IDs/names as were not in DB yet)
    # We use the existing the _build_mock_route_response but with better naming
    fastest_response = _build_mock_route_response(result["fastest_route"], "Fastest Route")
    eco_response = _build_mock_route_response(result["eco_friendly_route"], "Eco-Friendly Route")
    
    # Ensure vehicle_id is correctly set in mock responses
    fastest_response.vehicle_id = vehicle.id
    eco_response.vehicle_id = vehicle.id
    
    # Add back the delivery sequence for the frontend to know the order
    fastest_response.delivery_sequence = [delivery_points[i-1].id for i in result["fastest_route"]["route_sequence"][1:-1] if i > 0]
    eco_response.delivery_sequence = [delivery_points[i-1].id for i in result["eco_friendly_route"]["route_sequence"][1:-1] if i > 0]

    return RouteComparisonResponse(
        fastest_route=fastest_response,
        eco_friendly_route=eco_response,
        comparison=result["comparison"],
        pareto_optimal=result["pareto_optimal"],
        recommendation=result["recommendation"]
    )

def _save_route_to_db(db: Session, route_data: dict, vehicle_id: int, 
                      delivery_points: List[DeliveryPoint], route_type: str, user_id: int) -> OptimizedRoute:
    """Save optimized route to database"""
    
    # Create linestring geometry
    route_geom = create_linestring(route_data["route_coordinates"])
    
    # Create route
    db_route = OptimizedRoute(
        name=f"{route_type.title()} Route - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        route_type=route_type,
        vehicle_id=vehicle_id,
        route_geometry=route_geom,
        total_distance_km=route_data["total_distance_km"],
        total_duration_minutes=route_data["total_duration_minutes"],
        estimated_co2_kg=route_data["estimated_co2_kg"],
        estimated_fuel_liters=route_data["estimated_fuel_liters"],
        optimization_objective=route_data["objective"],
        constraints_applied={
            "max_capacity": True,
            "time_windows": False
        },
        status="planned",
        created_by_id=user_id,
        assigned_driver_id=user_id if db.query(User).filter(User.id == user_id).first().role == 'driver' else None
    )
    
    db.add(db_route)
    db.flush()  # Get the ID without committing
    
    # Associate delivery points with route in correct sequence
    for idx, point_idx in enumerate(route_data["route_sequence"][1:-1]):  # Skip depot start/end
        if point_idx > 0:  # Skip depot
            delivery_point = delivery_points[point_idx - 1]
            
            # Insert into association table with sequence
            stmt = route_delivery_points.insert().values(
                route_id=db_route.id,
                delivery_point_id=delivery_point.id,
                sequence_order=idx + 1
            )
            db.execute(stmt)
    
    db.commit()
    db.refresh(db_route)
    
    return db_route

def _build_route_response(db_route: OptimizedRoute, route_data: dict, 
                         delivery_points: List[DeliveryPoint]) -> OptimizedRouteResponse:
    """Build route response with segments"""
    
    # Build delivery sequence
    delivery_sequence = []
    for idx in route_data["route_sequence"][1:-1]:  # Skip depot
        if idx > 0:
            delivery_sequence.append(delivery_points[idx - 1].id)
    
    # Build route segments
    segments = []
    coords = route_data["route_coordinates"]
    
    for i in range(len(coords) - 1):
        # Interpolate points for smooth visualization
        interpolated = interpolate_route_points(coords[i], coords[i+1], num_points=5)
        
        # Determine point names
        if i == 0:
            from_name = "Start"
        elif i < len(delivery_points) + 1:
            from_name = delivery_points[route_data["route_sequence"][i] - 1].name if route_data["route_sequence"][i] > 0 else "Start"
        else:
            from_name = "Return"
        
        if i + 1 == len(coords) - 1:
            to_name = "End"
        elif i + 1 < len(delivery_points) + 1:
            to_name = delivery_points[route_data["route_sequence"][i+1] - 1].name if route_data["route_sequence"][i+1] > 0 else "End"
        else:
            to_name = "Return"
        
        segment = RouteSegment(
            from_point=from_name,
            to_point=to_name,
            distance_km=route_data["total_distance_km"] / (len(coords) - 1),  # Approximate
            duration_minutes=route_data["total_duration_minutes"] / (len(coords) - 1),
            co2_kg=route_data["estimated_co2_kg"] / (len(coords) - 1),
            coordinates=[[lon, lat] for lat, lon in interpolated]
        )
        segments.append(segment)
    
    return OptimizedRouteResponse(
        id=db_route.id,
        name=db_route.name,
        route_type=db_route.route_type,
        vehicle_id=db_route.vehicle_id,
        total_distance_km=db_route.total_distance_km,
        total_duration_minutes=db_route.total_duration_minutes,
        estimated_co2_kg=db_route.estimated_co2_kg,
        estimated_fuel_liters=db_route.estimated_fuel_liters,
        optimization_objective=db_route.optimization_objective,
        delivery_sequence=delivery_sequence,
        route_segments=segments,
        conditions=route_data.get("route_conditions"),
        created_at=db_route.created_at
    )

@router.get("/routes", response_model=List[OptimizedRouteResponse])
def get_optimized_routes(
    skip: int = 0,
    limit: int = 50,
    route_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all optimized routes"""
    
    query = db.query(OptimizedRoute)
    
    if route_type:
        query = query.filter(OptimizedRoute.route_type == route_type)
    
    routes = query.order_by(OptimizedRoute.created_at.desc()).offset(skip).limit(limit).all()
    
    # Build simplified responses
    responses = []
    for route in routes:
        responses.append(OptimizedRouteResponse(
            id=route.id,
            name=route.name,
            route_type=route.route_type,
            vehicle_id=route.vehicle_id,
            total_distance_km=route.total_distance_km,
            total_duration_minutes=route.total_duration_minutes,
            estimated_co2_kg=route.estimated_co2_kg,
            estimated_fuel_liters=route.estimated_fuel_liters,
            optimization_objective=route.optimization_objective,
            delivery_sequence=[],
            route_segments=[],
            created_at=route.created_at
        ))
    
    return responses

@router.get("/routes/{route_id}")
def get_route_details(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific route including geometry"""
    
    route = db.query(OptimizedRoute).filter(OptimizedRoute.id == route_id).first()
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Get associated delivery points
    points_query = db.query(DeliveryPoint, route_delivery_points.c.sequence_order)\
        .join(route_delivery_points, DeliveryPoint.id == route_delivery_points.c.delivery_point_id)\
        .filter(route_delivery_points.c.route_id == route.id)\
        .order_by(route_delivery_points.c.sequence_order).all()
    
    delivery_points = [p[0] for p in points_query]
    
    # Extract coordinates from geometry
    # We use a simple method since we're using shapely/geoalchemy2
    from geoalchemy2.shape import to_shape
    shape = to_shape(route.route_geometry)
    coords = [[point[0], point[1]] for point in shape.coords] # [[lon, lat], ...]
    
    # Reconstruct segments (simplified)
    segments = []
    if len(coords) > 1:
        # For now, we'll return the whole route as one main segment if reconstruction is complex
        segment = RouteSegment(
            from_point="Start",
            to_point="End",
            distance_km=route.total_distance_km,
            duration_minutes=route.total_duration_minutes,
            co2_kg=route.estimated_co2_kg,
            coordinates=coords
        )
        segments.append(segment)

    return {
        "id": route.id,
        "name": route.name,
        "route_type": route.route_type,
        "vehicle_id": route.vehicle_id,
        "total_distance_km": route.total_distance_km,
        "total_duration_minutes": route.total_duration_minutes,
        "estimated_co2_kg": route.estimated_co2_kg,
        "estimated_fuel_liters": route.estimated_fuel_liters,
        "status": route.status,
        "created_at": route.created_at,
        "route_segments": segments,
        "delivery_sequence": [p.id for p in delivery_points]
    }
@router.post("/assign/{route_id}")
def assign_route(
    route_id: int,
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign an optimized route to a specific driver"""
    if current_user.role != "manager" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only managers can assign routes")
    
    route = db.query(OptimizedRoute).filter(OptimizedRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    driver = db.query(User).filter(User.id == driver_id, User.role == "driver").first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    route.assigned_driver_id = driver_id
    db.commit()
    
    return {"message": f"Route assigned to {driver.full_name}"}

@router.post("/save-and-assign")
def save_and_assign_route(
    request: RouteAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save an ad-hoc calculated route and assign it to a driver"""
    if current_user.role != "manager" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only managers can assign routes")
    
    driver = db.query(User).filter(User.id == request.driver_id, User.role == "driver").first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    # Extract coordinates from segments to create Geometry
    all_coords = []
    for segment in request.route_data.route_segments:
        all_coords.extend([[c[1], c[0]] for c in segment.coordinates]) # Convert [lon, lat] back to [lat, lon] for create_linestring
    
    # Deduplicate sequential identical points if any
    unique_coords = []
    for c in all_coords:
        if not unique_coords or c != unique_coords[-1]:
            unique_coords.append(c)
            
    from app.services.route_optimizer import RouteOptimizer
    route_geom = create_linestring(unique_coords)
    
    # Create the persistent route
    route_name = f"{request.route_data.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    db_route = OptimizedRoute(
        name=route_name,
        route_type=request.route_data.route_type,
        vehicle_id=request.route_data.vehicle_id,
        route_geometry=route_geom,
        total_distance_km=request.route_data.total_distance_km,
        total_duration_minutes=request.route_data.total_duration_minutes,
        estimated_co2_kg=request.route_data.estimated_co2_kg,
        estimated_fuel_liters=request.route_data.estimated_fuel_liters,
        optimization_objective=request.route_data.optimization_objective,
        constraints_applied={},
        status="planned",
        created_by_id=current_user.id,
        assigned_driver_id=request.driver_id
    )
    
    db.add(db_route)
    db.flush()
    
    # Associate delivery points
    for idx, point_id in enumerate(request.route_data.delivery_sequence):
        stmt = route_delivery_points.insert().values(
            route_id=db_route.id,
            delivery_point_id=point_id,
            sequence_order=idx + 1
        )
        db.execute(stmt)
        
    db.commit()
    return {"message": f"Route saved and assigned to {driver.full_name}", "route_id": db_route.id}

@router.post("/direct", response_model=RouteComparisonResponse)
def optimize_direct_route(
    request: DirectRouteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate optimized routes for arbitrary coordinates (ad-hoc)
    Does not save to database.
    """
    
    # Map transport type to vehicle parameters
    transport_defaults = {
        "car": {"fuel_efficiency_kmpl": 15.0, "emission_factor": 2.31, "avg_speed_kmh": 60.0},
        "van": {"fuel_efficiency_kmpl": 10.0, "emission_factor": 2.68, "avg_speed_kmh": 50.0},
        "truck": {"fuel_efficiency_kmpl": 5.0, "emission_factor": 2.68, "avg_speed_kmh": 40.0},
        "ev": {"fuel_efficiency_kmpl": 999.0, "emission_factor": 0.05, "avg_speed_kmh": 60.0}
    }
    
    vehicle_data = transport_defaults.get(request.transport_type, transport_defaults["car"])
    
    # Prepare data for optimizer
    start_location = (request.start_location.latitude, request.start_location.longitude)
    delivery_locations = [(request.end_location.latitude, request.end_location.longitude)]
    
    # Run optimization
    optimizer = RouteOptimizer()
    result = optimizer.generate_pareto_solutions(
        start_location,
        delivery_locations,
        vehicle_data,
        max_duration_seconds=86400,  # 24 hours
        return_to_start=False
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Build responses (mocking IDs/names as it's not in DB)
    fastest_response = _build_mock_route_response(result["fastest_route"], "Fastest Personal Route")
    eco_response = _build_mock_route_response(result["eco_friendly_route"], "Eco Personal Route")
    
    return RouteComparisonResponse(
        fastest_route=fastest_response,
        eco_friendly_route=eco_response,
        comparison=result["comparison"],
        pareto_optimal=result["pareto_optimal"],
        recommendation=result["recommendation"]
    )

def _build_mock_route_response(route_data: dict, name: str) -> OptimizedRouteResponse:
    """Build a route response for non-persistent routes"""
    
    segments = []
    coords = route_data["route_coordinates"]
    
    if len(coords) > 1:
        segment = RouteSegment(
            from_point="Origin",
            to_point="Destination",
            distance_km=route_data["total_distance_km"],
            duration_minutes=route_data["total_duration_minutes"],
            co2_kg=route_data["estimated_co2_kg"],
            coordinates=[[lon, lat] for lat, lon in coords]
        )
        segments.append(segment)
        
    return OptimizedRouteResponse(
        id=0, # No DB ID
        name=name,
        route_type=route_data["objective"],
        vehicle_id=0,
        total_distance_km=route_data["total_distance_km"],
        total_duration_minutes=route_data["total_duration_minutes"],
        estimated_co2_kg=route_data["estimated_co2_kg"],
        estimated_fuel_liters=route_data["estimated_fuel_liters"],
        optimization_objective=route_data["objective"],
        delivery_sequence=[],
        route_segments=segments,
        conditions=route_data.get("route_conditions"),
        created_at=datetime.now()
    )
