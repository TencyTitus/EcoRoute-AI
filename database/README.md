# EcoRoute AI - Database Setup Guide

## Prerequisites

- PostgreSQL 14+ installed
- PostGIS extension available
- TimescaleDB extension available (optional but recommended)

## Installation Steps

### 1. Install PostgreSQL Extensions

```bash
# On Ubuntu/Debian
sudo apt-get install postgresql-14-postgis-3
sudo apt-get install timescaledb-postgresql-14

# On macOS with Homebrew
brew install postgis
brew install timescaledb

# On Windows
# Download and install PostGIS from https://postgis.net/windows_downloads/
# Download and install TimescaleDB from https://www.timescale.com/
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ecoroute_db;

# Connect to the database
\c ecoroute_db
```

### 3. Initialize Extensions

```bash
# Run the initialization script
psql -U postgres -d ecoroute_db -f database/init_extensions.sql
```

### 4. Create Tables

The tables will be automatically created by SQLAlchemy when you run the backend application for the first time.

```bash
cd backend
python run.py
```

### 5. Enable TimescaleDB Hypertable (After tables are created)

```sql
-- Connect to database
psql -U postgres -d ecoroute_db

-- Create hypertable for time-series data
SELECT create_hypertable('route_history', 'timestamp');
```

### 6. Load Seed Data

```bash
# Load sample data
psql -U postgres -d ecoroute_db -f database/seed_data.sql
```

## Database Configuration

Update your `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ecoroute_db
SECRET_KEY=your_secret_key_here
```

## Verify Installation

```sql
-- Check PostGIS version
SELECT PostGIS_Version();

-- Check TimescaleDB version
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Verify tables
\dt

-- Check sample data
SELECT COUNT(*) FROM vehicles;
SELECT COUNT(*) FROM delivery_points;
SELECT COUNT(*) FROM users;
```

## Test Credentials

After loading seed data, you can login with:

- **Admin**: admin@ecoroute.ai / admin123
- **Manager**: manager@ecoroute.ai / admin123
- **Driver**: driver1@ecoroute.ai / admin123

**Important**: Change these passwords in production!

## Troubleshooting

### PostGIS not found
```sql
CREATE EXTENSION postgis;
```

### TimescaleDB not found
```sql
CREATE EXTENSION timescaledb;
```

### Permission denied
```bash
# Grant permissions to your user
GRANT ALL PRIVILEGES ON DATABASE ecoroute_db TO your_user;
```
