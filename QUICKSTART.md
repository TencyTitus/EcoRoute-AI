# EcoRoute AI - Quick Start Guide

## 🚀 Getting Started

### 1. Database Setup (5 minutes)

```bash
# Create PostgreSQL database
createdb ecoroute_db

# Initialize extensions
psql -d ecoroute_db -f database/init_extensions.sql

# The backend will create tables automatically on first run
# After tables are created, load seed data:
psql -d ecoroute_db -f database/seed_data.sql
```

### 2. Backend Setup (2 minutes)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ecoroute_db" > .env
echo "SECRET_KEY=your_secret_key_here" >> .env

# Run backend (already running in your case)
python run.py
```

Backend will be at: http://127.0.0.1:8000

### 3. Frontend Setup (Already Done!)

```bash
cd frontend

# Dependencies already installed!
# Just ensure .env has Mapbox token
echo "REACT_APP_MAPBOX_TOKEN=your_mapbox_token" > .env

# Already running at http://localhost:3000
```

## 🎯 Test the System

### Login Credentials
- **Manager**: manager@ecoroute.ai / admin123
- **Admin**: admin@ecoroute.ai / admin123
- **Driver**: driver1@ecoroute.ai / admin123

### Try Route Optimization

1. **Login** as manager
2. Go to **Route Planner** (new menu item!)
3. **Add delivery points** or use the 10 pre-loaded Delhi NCR locations
4. **Select a vehicle** from the 6 pre-loaded vehicles
5. **Check delivery points** you want to include
6. Click **"Optimize Route"**
7. **View comparison** between fastest and eco-friendly routes
8. **See savings** in CO₂ and time trade-offs

### Check Analytics

1. Go to **Analytics** page
2. See **real charts** with Chart.js:
   - Emission trends over time
   - Route type comparison
   - Vehicle efficiency
   - Fleet performance
3. Change time period (7/30/90 days)

## 📊 What's New

### Backend
✅ Route optimization with OR-Tools  
✅ Multi-objective VRP solver  
✅ Geospatial utilities  
✅ Mock traffic & weather APIs  
✅ Analytics endpoints  
✅ Delivery points management  

### Frontend
✅ Route Planner page  
✅ Chart.js visualizations  
✅ Enhanced Analytics dashboard  
✅ Route comparison UI  
✅ Delivery point management  

### Database
✅ PostGIS integration  
✅ TimescaleDB ready  
✅ Sample data loaded  
✅ Spatial indexes  

## 🔧 API Endpoints

**New Routes:**
- `POST /optimization/optimize` - Generate routes
- `GET /optimization/routes` - List routes
- `POST /delivery-points/` - Add delivery point
- `GET /analytics/fleet-performance` - Fleet metrics
- `GET /analytics/emission-trends` - Trends data

**API Docs:** http://127.0.0.1:8000/docs

## 💡 Next Steps

1. **Test route optimization** with sample data
2. **Add your own vehicles** in Vehicles page
3. **Create delivery points** for your area
4. **View analytics** to see trends
5. **Integrate real APIs** (traffic, weather) when ready
6. **Add ML model** for emission prediction later

## 🐛 Troubleshooting

**Backend errors?**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Run `pip install -r requirements.txt` again

**Frontend errors?**
- Run `npm install` in frontend directory
- Check console for errors
- Verify backend is running

**Charts not showing?**
- Dependencies installed: ✅ (just completed)
- Restart frontend: `npm start`
- Check browser console

## 📚 Documentation

- [Full README](file:///d:/EcoRoute-AI/README.md)
- [Database Setup](file:///d:/EcoRoute-AI/database/README.md)
- [Implementation Walkthrough](file:///C:/Users/tency/.gemini/antigravity/brain/1d5390e9-aa31-4fbe-bb82-bbb496742fbf/walkthrough.md)
