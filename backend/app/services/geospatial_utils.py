"""
Geospatial utility functions for EcoRoute AI
Handles distance calculations, elevation queries, and coordinate transformations
"""

import math
from typing import List, Tuple, Optional
from shapely.geometry import Point, LineString
from geopy.distance import geodesic

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth (in kilometers)
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
    
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    radius = 6371.0
    
    return radius * c

def calculate_route_distance(coordinates: List[Tuple[float, float]]) -> float:
    """
    Calculate total distance of a route given a list of coordinates
    
    Args:
        coordinates: List of (latitude, longitude) tuples
    
    Returns:
        Total distance in kilometers
    """
    total_distance = 0.0
    for i in range(len(coordinates) - 1):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[i + 1]
        total_distance += haversine_distance(lat1, lon1, lat2, lon2)
    
    return total_distance

def create_linestring(coordinates: List[Tuple[float, float]]) -> str:
    """
    Create a WKT LineString from coordinates for PostGIS storage
    
    Args:
        coordinates: List of (latitude, longitude) tuples
    
    Returns:
        WKT LineString representation
    """
    # Convert to (lon, lat) for WKT format
    points = [f"{lon} {lat}" for lat, lon in coordinates]
    return f"LINESTRING({', '.join(points)})"

def create_point_wkt(latitude: float, longitude: float) -> str:
    """
    Create a WKT Point from coordinates for PostGIS storage
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        WKT Point representation
    """
    return f"POINT({longitude} {latitude})"

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing between two points
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
    
    Returns:
        Bearing in degrees (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)
    
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def get_mock_elevation(latitude: float, longitude: float) -> float:
    """
    Mock elevation function - returns simulated elevation based on coordinates
    In production, this would query PostGIS elevation data
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Elevation in meters
    """
    # Simple mock: use sine wave based on latitude
    base_elevation = 100 + (50 * math.sin(math.radians(latitude * 10)))
    return max(0, base_elevation)

def calculate_elevation_gain(coordinates: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate total elevation gain and loss for a route
    
    Args:
        coordinates: List of (latitude, longitude) tuples
    
    Returns:
        Tuple of (total_gain_meters, total_loss_meters)
    """
    total_gain = 0.0
    total_loss = 0.0
    
    elevations = [get_mock_elevation(lat, lon) for lat, lon in coordinates]
    
    for i in range(len(elevations) - 1):
        diff = elevations[i + 1] - elevations[i]
        if diff > 0:
            total_gain += diff
        else:
            total_loss += abs(diff)
    
    return total_gain, total_loss

def interpolate_route_points(start: Tuple[float, float], end: Tuple[float, float], num_points: int = 10) -> List[Tuple[float, float]]:
    """
    Interpolate points between start and end coordinates
    Useful for creating smooth route visualizations
    
    Args:
        start: (latitude, longitude) of start point
        end: (latitude, longitude) of end point
        num_points: Number of intermediate points to generate
    
    Returns:
        List of interpolated (latitude, longitude) tuples
    """
    lat1, lon1 = start
    lat2, lon2 = end
    
    points = []
    for i in range(num_points + 1):
        fraction = i / num_points
        lat = lat1 + (lat2 - lat1) * fraction
        lon = lon1 + (lon2 - lon1) * fraction
        points.append((lat, lon))
    
    return points
