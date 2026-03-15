"""
External API integration services for traffic and weather data
Currently using mock data - can be replaced with real API calls
"""

import random
from typing import Dict, Optional
from datetime import datetime

class TrafficService:
    """Mock traffic data service - simulates real-time traffic conditions"""
    
    @staticmethod
    def get_traffic_speed(lat: float, lon: float, time: Optional[datetime] = None) -> Dict:
        """
        Get traffic speed for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            time: Time for traffic query (defaults to now)
        
        Returns:
            Dict with traffic information
        """
        # Mock traffic based on time of day
        if time is None:
            time = datetime.now()
        
        hour = time.hour
        
        # Simulate rush hour traffic
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            congestion_factor = random.uniform(0.5, 0.7)  # Heavy traffic
            condition = "heavy"
        elif 10 <= hour <= 16:
            congestion_factor = random.uniform(0.8, 0.95)  # Moderate traffic
            condition = "moderate"
        else:
            congestion_factor = random.uniform(0.95, 1.0)  # Light traffic
            condition = "light"
        
        base_speed = 50.0  # km/h
        current_speed = base_speed * congestion_factor
        
        return {
            "speed_kmh": round(current_speed, 2),
            "congestion_factor": round(congestion_factor, 2),
            "condition": condition,
            "timestamp": time.isoformat()
        }
    
    @staticmethod
    def get_route_traffic(coordinates: list) -> float:
        """
        Get average traffic speed for a route
        
        Args:
            coordinates: List of (lat, lon) tuples
        
        Returns:
            Average speed in km/h
        """
        speeds = []
        for lat, lon in coordinates:
            traffic_data = TrafficService.get_traffic_speed(lat, lon)
            speeds.append(traffic_data["speed_kmh"])
        
        return sum(speeds) / len(speeds) if speeds else 50.0


class WeatherService:
    """Mock weather data service - simulates weather conditions"""
    
    @staticmethod
    def get_weather(lat: float, lon: float, time: Optional[datetime] = None) -> Dict:
        """
        Get weather conditions for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            time: Time for weather query (defaults to now)
        
        Returns:
            Dict with weather information
        """
        # Mock weather conditions
        conditions = ["clear", "cloudy", "rainy", "foggy"]
        weights = [0.5, 0.3, 0.15, 0.05]
        
        condition = random.choices(conditions, weights=weights)[0]
        
        # Temperature varies by latitude (rough approximation)
        base_temp = 25 - (abs(lat) / 90) * 30
        temperature = base_temp + random.uniform(-5, 5)
        
        # Wind speed
        wind_speed = random.uniform(0, 20)
        
        # Precipitation (higher if rainy)
        precipitation = random.uniform(5, 20) if condition == "rainy" else 0
        
        return {
            "condition": condition,
            "temperature_celsius": round(temperature, 1),
            "wind_speed_kmh": round(wind_speed, 1),
            "precipitation_mm": round(precipitation, 1),
            "humidity_percent": random.randint(40, 90),
            "timestamp": (time or datetime.now()).isoformat()
        }
    
    @staticmethod
    def get_weather_impact_factor(weather_data: Dict) -> float:
        """
        Calculate weather impact on fuel consumption
        
        Args:
            weather_data: Weather data dict from get_weather()
        
        Returns:
            Multiplier factor (1.0 = no impact, >1.0 = increased consumption)
        """
        factor = 1.0
        
        # Rain increases fuel consumption
        if weather_data["condition"] == "rainy":
            factor += 0.1
        
        # Fog increases fuel consumption (slower speeds)
        if weather_data["condition"] == "foggy":
            factor += 0.15
        
        # Strong wind increases fuel consumption
        if weather_data["wind_speed_kmh"] > 30:
            factor += 0.05
        
        # Extreme temperatures affect efficiency
        temp = weather_data["temperature_celsius"]
        if temp < 0 or temp > 35:
            factor += 0.08
        
        return factor


class MockAPIService:
    """Combined service for easy access to mock APIs"""
    
    def __init__(self):
        self.traffic = TrafficService()
        self.weather = WeatherService()
    
    def get_route_conditions(self, coordinates: list) -> Dict:
        """
        Get comprehensive conditions for a route
        
        Args:
            coordinates: List of (lat, lon) tuples
        
        Returns:
            Dict with traffic and weather data
        """
        # Sample middle point for weather
        mid_idx = len(coordinates) // 2
        mid_lat, mid_lon = coordinates[mid_idx] if coordinates else (0, 0)
        
        avg_traffic_speed = self.traffic.get_route_traffic(coordinates)
        weather_data = self.weather.get_weather(mid_lat, mid_lon)
        weather_impact = self.weather.get_weather_impact_factor(weather_data)
        
        return {
            "avg_traffic_speed_kmh": avg_traffic_speed,
            "weather": weather_data,
            "weather_impact_factor": weather_impact,
            "traffic_impact_factor": avg_traffic_speed / 50.0  # Normalized to base speed
        }
