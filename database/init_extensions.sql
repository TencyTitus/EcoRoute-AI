-- Initialize PostGIS extension for geospatial support
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable TimescaleDB extension for time-series data (OPTIONAL)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create hypertable for route_history (time-series data)
-- Note: This should be run AFTER the route_history table is created by SQLAlchemy
-- AND ONLY if TimescaleDB extension is enabled.
-- SELECT create_hypertable('route_history', 'timestamp');

-- Create spatial indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_delivery_points_location 
ON delivery_points USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_optimized_routes_geometry 
ON optimized_routes USING GIST (route_geometry);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_optimized_routes_vehicle_id 
ON optimized_routes(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_optimized_routes_created_at 
ON optimized_routes(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_optimized_routes_route_type 
ON optimized_routes(route_type);

CREATE INDEX IF NOT EXISTS idx_route_history_route_id 
ON route_history(route_id);

CREATE INDEX IF NOT EXISTS idx_route_history_timestamp 
ON route_history(timestamp DESC);

-- Function to calculate distance between two points
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
DECLARE
    earth_radius CONSTANT DOUBLE PRECISION := 6371.0; -- km
    dlat DOUBLE PRECISION;
    dlon DOUBLE PRECISION;
    a DOUBLE PRECISION;
    c DOUBLE PRECISION;
BEGIN
    dlat := radians(lat2 - lat1);
    dlon := radians(lon2 - lon1);
    
    a := sin(dlat/2) * sin(dlat/2) + 
         cos(radians(lat1)) * cos(radians(lat2)) * 
         sin(dlon/2) * sin(dlon/2);
    
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    
    RETURN earth_radius * c;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- View for route performance summary
CREATE OR REPLACE VIEW route_performance_summary AS
SELECT 
    r.id,
    r.name,
    r.route_type,
    r.total_distance_km,
    r.total_duration_minutes,
    r.estimated_co2_kg,
    r.status,
    r.created_at,
    v.license_plate,
    v.vehicle_type,
    COUNT(DISTINCT rdp.delivery_point_id) as delivery_count
FROM optimized_routes r
LEFT JOIN vehicles v ON r.vehicle_id = v.id
LEFT JOIN route_delivery_points rdp ON r.id = rdp.route_id
GROUP BY r.id, r.name, r.route_type, r.total_distance_km, 
         r.total_duration_minutes, r.estimated_co2_kg, r.status, 
         r.created_at, v.license_plate, v.vehicle_type;

COMMENT ON EXTENSION postgis IS 'PostGIS extension for geospatial data support';
COMMENT ON FUNCTION calculate_distance IS 'Calculate Haversine distance between two lat/lon points in kilometers';
COMMENT ON VIEW route_performance_summary IS 'Summary view of route performance metrics';
