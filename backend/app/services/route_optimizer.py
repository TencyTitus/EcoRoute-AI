"""
Route optimization service using OR-Tools
Implements multi-objective Vehicle Routing Problem (VRP) solver
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Dict, Tuple, Optional
import math
import math
import logging
from app.services.geospatial_utils import haversine_distance
from app.services.external_apis import MockAPIService
from app.ml.co2_predictor import predictor

logger = logging.getLogger(__name__)

class RouteOptimizer:
    """Multi-objective route optimizer using OR-Tools VRP solver and ML predictions"""
    
    def __init__(self):
        self.api_service = MockAPIService()
        self.predictor = predictor
    
    def create_distance_matrix(self, locations: List[Tuple[float, float]]) -> List[List[float]]:
        """
        Create distance matrix between all locations
        
        Args:
            locations: List of (latitude, longitude) tuples
        
        Returns:
            2D matrix of distances in meters
        """
        num_locations = len(locations)
        distance_matrix = [[0] * num_locations for _ in range(num_locations)]
        
        for i in range(num_locations):
            for j in range(num_locations):
                if i != j:
                    lat1, lon1 = locations[i]
                    lat2, lon2 = locations[j]
                    distance_km = haversine_distance(lat1, lon1, lat2, lon2)
                    distance_matrix[i][j] = int(distance_km * 1000)  # Convert to meters
        
        return distance_matrix
    
    def create_time_matrix(self, locations: List[Tuple[float, float]], avg_speed_kmh: float = 50.0) -> List[List[int]]:
        """
        Create time matrix between all locations based on distance and speed.
        Uses a road distance multiplier (1.4x) to convert straight-line haversine
        distance to realistic road distance.
        
        Args:
            locations: List of (latitude, longitude) tuples
            avg_speed_kmh: Average vehicle speed
        
        Returns:
            2D matrix of travel times in seconds
        """
        distance_matrix = self.create_distance_matrix(locations)
        num_locations = len(locations)
        time_matrix = [[0] * num_locations for _ in range(num_locations)]
        
        # Get traffic conditions — returns average speed in km/h
        traffic_speed_kmh = self.api_service.traffic.get_route_traffic(locations)
        
        # Use the lower of vehicle speed and traffic speed, with a minimum of 10 km/h
        effective_speed = max(min(avg_speed_kmh, traffic_speed_kmh), 10.0)
        
        # Road distance multiplier: real roads are ~1.4x longer than straight-line
        ROAD_FACTOR = 1.4
        
        for i in range(num_locations):
            for j in range(num_locations):
                if i != j:
                    straight_line_km = distance_matrix[i][j] / 1000.0
                    road_distance_km = straight_line_km * ROAD_FACTOR
                    time_hours = road_distance_km / effective_speed
                    time_matrix[i][j] = int(time_hours * 3600)  # Convert to seconds
        
        return time_matrix
    
    def calculate_emission_factor(self, distance_km: float, vehicle_data: Dict, 
                                   traffic_factor: float = 1.0, weather_factor: float = 1.0) -> float:
        """
        Calculate CO2 emissions for a route segment using Unified Machine Learning.
        Combines Vehicle Model + Traffic Prediction Model.
        """
        # 1. PREDICT: Base Engine Emission (g/km)
        engine_size = vehicle_data.get('engine_size', 2.0)
        cylinders = vehicle_data.get('cylinders', 4)
        fuel_kmpl = vehicle_data.get('fuel_efficiency_kmpl', 10.0)
        
        base_emission_g_km = self.predictor.predict_co2(engine_size, cylinders, fuel_kmpl)
        
        # 2. PREDICT: Environmental Traffic Impact
        # We ask the ML model: "Based on current time and weather, what's the traffic load?"
        ml_traffic_impact = self.predictor.predict_traffic_impact(
            temp=293.15, # 20°C in Kelvin (Dataset uses Kelvin)
            weather="Clear" # This would ideally come from a Weather API
        )
        
        # 3. CALCULATE: Final Real-World Emission
        # We combine ML Traffic + Manual Overrides (if any)
        total_impact = ml_traffic_impact * traffic_factor * weather_factor
        
        adjusted_emission_g_km = base_emission_g_km * total_impact
        
        # 4. Result in kg
        co2_kg = (adjusted_emission_g_km * distance_km) / 1000.0
        
        return co2_kg
    
    def optimize_route(self, 
                      start_location: Tuple[float, float],
                      delivery_locations: List[Tuple[float, float]],
                      vehicle_data: Dict,
                      objective: str = "time",
                      max_duration_seconds: int = 28800,
                      return_to_start: bool = True) -> Dict:
        """
        Optimize route using OR-Tools VRP solver
        
        Args:
            start_location: Starting point (lat, lon)
            delivery_locations: List of delivery points (lat, lon)
            vehicle_data: Vehicle characteristics
            objective: 'time' or 'emission'
            max_duration_seconds: Maximum route duration
            return_to_start: Whether to return to starting location
        
        Returns:
            Dict with optimized route information
        """
        # Combine all locations (depot + deliveries)
        all_locations = [start_location] + delivery_locations
        num_locations = len(all_locations)
        logger.info(f"Optimizing route with {num_locations} locations for objective {objective}")
        logger.info(f"start_location: {start_location}")
        logger.info(f"delivery_locations: {delivery_locations}")
        
        # Create distance and time matrices
        distance_matrix = self.create_distance_matrix(all_locations)
        time_matrix = self.create_time_matrix(all_locations, vehicle_data.get('avg_speed_kmh', 50.0))
        logger.info(f"Distance matrix: {distance_matrix}")
        
        # Get environmental conditions
        route_conditions = self.api_service.get_route_conditions(all_locations)
        
        # Create routing model
        if return_to_start:
            manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)  # 1 vehicle, depot (start/end) at 0
            routing = pywrapcp.RoutingModel(manager)
        else:
            # Add a virtual end node to allow ending at any delivery location
            # This node index will be num_locations
            manager = pywrapcp.RoutingIndexManager(num_locations + 1, 1, [0], [num_locations])
            routing = pywrapcp.RoutingModel(manager)
        
        # Define time callback (used for time dimension in all cases)
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            
            # If going to or from virtual node, cost is 0
            if from_node == num_locations or to_node == num_locations:
                return 0
                
            return time_matrix[from_node][to_node]
            
        transit_callback_index = routing.RegisterTransitCallback(time_callback)

        # Define cost callback based on objective
        if objective == "time":
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
        elif objective == "emission":
            # Use distance weighted by emission factors for the cost
            def emission_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                
                # If going to or from virtual node, cost is 0
                if from_node == num_locations or to_node == num_locations:
                    return 0
                
                distance_km = distance_matrix[from_node][to_node] / 1000.0
                
                emission = self.calculate_emission_factor(
                    distance_km, 
                    vehicle_data,
                    route_conditions['traffic_impact_factor'],
                    route_conditions['weather_impact_factor']
                )
                return int(emission * 1000)  # Scale to integer
            
            cost_callback_index = routing.RegisterTransitCallback(emission_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(cost_callback_index)
        
        # Add time constraint
        routing.AddDimension(
            transit_callback_index, # Always use time_callback for Time dimension
            0,  # no slack
            max_duration_seconds,
            True,  # start cumul to zero
            'Time'
        )
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 10
        
        # Solve
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self._extract_solution(manager, routing, solution, all_locations, 
                                         distance_matrix, time_matrix, vehicle_data, 
                                         route_conditions, objective)
        else:
            return {"error": f"No solution found for {objective} optimization. The distance might be too long for an {max_duration_seconds//3600}-hour shift."}
    
    def _extract_solution(self, manager, routing, solution, locations, distance_matrix, 
                         time_matrix, vehicle_data, route_conditions, objective) -> Dict:
        """Extract solution details from OR-Tools solver"""
        
        route_sequence = []
        route_coordinates = []
        total_distance = 0
        total_time = 0
        total_emission = 0
        num_locations = len(locations)
        
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_sequence.append(node)
            route_coordinates.append(locations[node])
            
            next_index = solution.Value(routing.NextVar(index))
            next_node = manager.IndexToNode(next_index)
            
            if not routing.IsEnd(next_index):
                # Add segment metrics
                segment_distance = distance_matrix[node][next_node] / 1000.0  # km
                segment_time = time_matrix[node][next_node]  # seconds
                segment_emission = self.calculate_emission_factor(
                    segment_distance,
                    vehicle_data,
                    route_conditions['traffic_impact_factor'],
                    route_conditions['weather_impact_factor']
                )
                
                total_distance += segment_distance
                total_time += segment_time
                total_emission += segment_emission
            
            index = next_index
        
        # Add final node
        final_node = manager.IndexToNode(index)
        if final_node < num_locations:
            route_sequence.append(final_node)
            route_coordinates.append(locations[final_node])
        
        # Road distance factor: real roads are ~1.4x longer than straight-line haversine
        ROAD_FACTOR = 1.4
        road_distance = total_distance * ROAD_FACTOR
        
        # Calculate fuel consumption based on road distance
        fuel_efficiency = vehicle_data.get('fuel_efficiency_kmpl', 10.0)
        total_fuel = road_distance / fuel_efficiency
        
        return {
            "success": True,
            "objective": objective,
            "route_sequence": route_sequence,
            "route_coordinates": route_coordinates,
            "total_distance_km": round(road_distance, 2),
            "total_duration_minutes": round(total_time / 60, 2),
            "estimated_co2_kg": round(total_emission, 2),
            "estimated_fuel_liters": round(total_fuel, 2),
            "avg_speed_kmh": round((road_distance / (total_time / 3600)) if total_time > 0 else 0, 2),
            "route_conditions": route_conditions,
            "num_stops": len(route_sequence) - 2  # Exclude start and end depot
        }
    
    def generate_pareto_solutions(self, start_location: Tuple[float, float],
                                  delivery_locations: List[Tuple[float, float]],
                                  vehicle_data: Dict,
                                  max_duration_seconds: int = 28800,
                                  return_to_start: bool = True) -> Dict:
        """
        Generate both time-optimized and emission-optimized routes for comparison
        
        Args:
            start_location: Starting point
            delivery_locations: Delivery points
            vehicle_data: Vehicle characteristics
        
        Returns:
            Dict with both routes and comparison metrics
        """
        # Optimize for time
        fastest_route = self.optimize_route(
            start_location, delivery_locations, vehicle_data, objective="time",
            max_duration_seconds=max_duration_seconds,
            return_to_start=return_to_start
        )
        
        # Optimize for emissions
        eco_route = self.optimize_route(
            start_location, delivery_locations, vehicle_data, objective="emission",
            max_duration_seconds=max_duration_seconds,
            return_to_start=return_to_start
        )
        
        # Calculate comparison metrics
        if fastest_route.get("success") and eco_route.get("success"):
            # ... (comparison logic)
            co2_savings = fastest_route["estimated_co2_kg"] - eco_route["estimated_co2_kg"]
            co2_savings_percent = (co2_savings / fastest_route["estimated_co2_kg"]) * 100 if fastest_route["estimated_co2_kg"] > 0 else 0
            
            time_difference = eco_route["total_duration_minutes"] - fastest_route["total_duration_minutes"]
            time_difference_percent = (time_difference / fastest_route["total_duration_minutes"]) * 100 if fastest_route["total_duration_minutes"] > 0 else 0
            
            comparison = {
                "fastest_route_co2_kg": fastest_route["estimated_co2_kg"],
                "eco_route_co2_kg": eco_route["estimated_co2_kg"],
                "co2_savings_kg": round(co2_savings, 2),
                "co2_savings_percent": round(co2_savings_percent, 2),
                "fastest_route_time_min": fastest_route["total_duration_minutes"],
                "eco_route_time_min": eco_route["total_duration_minutes"],
                "time_difference_min": round(time_difference, 2),
                "time_difference_percent": round(time_difference_percent, 2)
            }
            
            # Generate recommendation
            if co2_savings_percent > 15 and time_difference_percent < 10:
                recommendation = "Eco-friendly route recommended: Significant emission savings with minimal time increase"
            elif time_difference_percent < 5:
                recommendation = "Eco-friendly route recommended: Minimal time trade-off"
            elif co2_savings_percent < 5:
                recommendation = "Fastest route recommended: Minimal emission difference"
            else:
                recommendation = f"Trade-off decision: Save {co2_savings_percent:.1f}% emissions at cost of {time_difference_percent:.1f}% more time"
            
            return {
                "fastest_route": fastest_route,
                "eco_friendly_route": eco_route,
                "comparison": comparison,
                "recommendation": recommendation,
                "pareto_optimal": True
            }
        else:
            err_msg = fastest_route.get("error") or eco_route.get("error") or "Failed to generate one or both routes"
            logger.error(f"Pareto generation failed: {err_msg}")
            return {
                "error": err_msg,
                "fastest_route": fastest_route,
                "eco_friendly_route": eco_route
            }
