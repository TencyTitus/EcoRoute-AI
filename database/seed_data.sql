-- Sample vehicles with different characteristics
INSERT INTO vehicles (vehicle_type, license_plate, model, year, fuel_type, emission_factor, fuel_efficiency_kmpl, max_capacity_kg, avg_speed_kmh, status)
VALUES
    ('truck', 'MH-12-AB-1234', 'Tata LPT 1613', 2022, 'diesel', 2.68, 8.5, 15000, 45, 'available'),
    ('truck', 'KA-03-CD-5678', 'Ashok Leyland 1920', 2021, 'diesel', 2.68, 7.8, 20000, 42, 'available'),
    ('van', 'DL-01-EF-9012', 'Mahindra Supro', 2023, 'diesel', 2.68, 12.0, 5000, 55, 'available'),
    ('van', 'TN-18-GH-3456', 'Maruti Eeco', 2022, 'petrol', 2.31, 15.0, 500, 60, 'available'),
    ('truck', 'MH-14-IJ-7890', 'Eicher Pro 3015', 2020, 'diesel', 2.68, 9.2, 12000, 48, 'maintenance'),
    ('electric', 'KA-05-KL-2345', 'Tata Ace EV', 2023, 'electric', 0.0, 100.0, 750, 50, 'available')
ON CONFLICT (license_plate) DO NOTHING;

-- Sample delivery points in Delhi NCR region
INSERT INTO delivery_points (name, address, latitude, longitude, location, demand, service_time, priority)
VALUES
    ('Connaught Place Hub', 'Connaught Place, New Delhi', 28.6315, 77.2167, ST_SetSRID(ST_MakePoint(77.2167, 28.6315), 4326), 500, 600, 2),
    ('Karol Bagh Market', 'Karol Bagh, Delhi', 28.6519, 77.1900, ST_SetSRID(ST_MakePoint(77.1900, 28.6519), 4326), 300, 450, 1),
    ('Rohini Sector 7', 'Rohini, Delhi', 28.7041, 77.1025, ST_SetSRID(ST_MakePoint(77.1025, 28.7041), 4326), 450, 500, 2),
    ('Dwarka Sector 10', 'Dwarka, New Delhi', 28.5921, 77.0460, ST_SetSRID(ST_MakePoint(77.0460, 28.5921), 4326), 600, 550, 3),
    ('Noida Sector 18', 'Noida, Uttar Pradesh', 28.5677, 77.3206, ST_SetSRID(ST_MakePoint(77.3206, 28.5677), 4326), 400, 480, 2),
    ('Gurgaon Cyber City', 'Gurgaon, Haryana', 28.4950, 77.0826, ST_SetSRID(ST_MakePoint(77.0826, 28.4950), 4326), 550, 600, 3),
    ('Saket District Centre', 'Saket, New Delhi', 28.5244, 77.2066, ST_SetSRID(ST_MakePoint(77.2066, 28.5244), 4326), 350, 420, 1),
    ('Lajpat Nagar Market', 'Lajpat Nagar, Delhi', 28.5678, 77.2436, ST_SetSRID(ST_MakePoint(77.2436, 28.5678), 4326), 280, 400, 1),
    ('Vasant Kunj Mall', 'Vasant Kunj, Delhi', 28.5200, 77.1588, ST_SetSRID(ST_MakePoint(77.1588, 28.5200), 4326), 420, 480, 2),
    ('Greater Noida Warehouse', 'Greater Noida, UP', 28.4744, 77.5040, ST_SetSRID(ST_MakePoint(77.5040, 28.4744), 4326), 700, 650, 3)
ON CONFLICT DO NOTHING;

-- Sample admin user (password: admin123)
-- Hash generated using bcrypt
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES
    ('System Admin', 'admin@ecoroute.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr.oaLQKa', 'admin', true),
    ('Fleet Manager', 'manager@ecoroute.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr.oaLQKa', 'manager', true),
    ('Driver One', 'driver1@ecoroute.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIr.oaLQKa', 'driver', true)
ON CONFLICT (email) DO NOTHING;

-- Note: All sample users have password 'admin123' for testing purposes
-- In production, users should set their own secure passwords
