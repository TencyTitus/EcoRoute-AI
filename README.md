# EcoRoute AI - Setup and Running Guide

## 🧠 Machine Learning Integration

The project now includes an **ML-powered CO2 Emission Predictor**. Instead of using simple multipliers, it uses a **Random Forest** regression model trained on real-world vehicle data.

### How it works:
1. **Training**: We use the `ml/CO2 Emissions_Canada.csv` dataset, which contains metrics for thousands of vehicles.
2. **Features**: The model predicts emissions based on:
   - **Engine Size (L)**
   - **Number of Cylinders**
   - **Combined Fuel Consumption (L/100 km)**
3. **Accuracy**: The Random Forest model captures the non-linear relationship between engine power and emissions more accurately than a linear formula.

### How to update the ML Model:
If you add more data to your CSV files, you can retrain the model by running:
```bash
# In the backend directory
python app/ml/train_co2_model.py
```

### ML Files:
- `backend/app/ml/train_co2_model.py`: The "Smart Trainer" that creates the model.
- `backend/app/ml/co2_model.joblib`: The saved "Brain" file.
- `backend/app/ml/co2_predictor.py`: The service that serves predictions to the app.

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 14+ with PostGIS and TimescaleDB extensions

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ecoroute_db
SECRET_KEY=your_secret_key_here_use_strong_random_string
```

### 3. Initialize Database

Follow the instructions in `database/README.md` to set up PostgreSQL with PostGIS and TimescaleDB.

### 4. Run Backend

```bash
cd backend
python run.py
```

The backend API will be available at `http://127.0.0.1:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env` file in the `frontend` directory:

```env
REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
```

Get a Mapbox token from: https://www.mapbox.com/

### 3. Run Frontend

```bash
cd frontend
npm start
```

The frontend will be available at `http://localhost:3000`

## Features Implemented

### ✅ Backend
- Multi-objective route optimization using OR-Tools
- Geospatial utilities with PostGIS integration
- Mock traffic and weather APIs
- Delivery point management
- Vehicle management with capacity constraints
- Analytics endpoints for fleet performance
- Route history and performance logging
- JWT authentication with role-based access

### ✅ Frontend
- Route planner with delivery point management
- Vehicle selection and optimization requests
- Route comparison (Fastest vs Eco-Friendly)
- Real-time analytics with Chart.js visualizations
- Emission trends and fleet performance charts
- Role-based dashboards (Admin, Manager, Driver)
- Interactive Mapbox integration

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Test Accounts

After loading seed data:
- **Admin**: admin@ecoroute.ai / admin123
- **Manager**: manager@ecoroute.ai / admin123
- **Driver**: driver1@ecoroute.ai / admin123

## Usage Workflow

1. **Login** as manager (manager@ecoroute.ai)
2. **Add Vehicles** in the Vehicles page
3. **Add Delivery Points** in the Route Planner
4. **Optimize Routes** by selecting vehicle and delivery points
5. **View Results** comparing fastest vs eco-friendly routes
6. **Check Analytics** for fleet performance and emission trends

## Future Enhancements

- [ ] ML model for emission prediction
- [ ] Real traffic API integration (Google Maps, TomTom)
- [ ] Real weather API integration (OpenWeatherMap)
- [ ] TimescaleDB continuous aggregates for analytics
- [ ] Route execution tracking
- [ ] Mobile app for drivers
- [ ] Advanced route constraints (time windows, vehicle compatibility)

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Ensure all Python dependencies are installed

### Frontend won't start
- Check Node.js version (16+)
- Run `npm install` again
- Clear node_modules and reinstall

### Routes not optimizing
- Ensure at least one vehicle exists
- Add at least 2 delivery points
- Check backend logs for errors

### Charts not displaying
- Ensure Chart.js dependencies installed
- Check browser console for errors
- Verify analytics API endpoints are working

## Support

For issues or questions, check the implementation plan and task list in the artifacts directory.
