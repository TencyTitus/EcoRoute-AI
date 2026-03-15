import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Config Paths
ML_DIR = r"d:\EcoRoute-AI\ml"
BACKEND_ML_DIR = r"d:\EcoRoute-AI\backend\app\ml"

# Files
CO2_FILE = os.path.join(ML_DIR, "CO2 Emissions_Canada.csv")
TRAFFIC_FILE = os.path.join(ML_DIR, "Metro_Interstate_Traffic_Volume.csv")

def train_unified_ml():
    print("🧠 Starting Unified ML Training Pipeline...")
    
    if not os.path.exists(BACKEND_ML_DIR):
        os.makedirs(BACKEND_ML_DIR)

    # --- PART 1: VEHICLE EMISSIONS MODEL ---
    print("\n🚗 Training Vehicle Emission Model...")
    df_co2 = pd.read_csv(CO2_FILE)
    
    # Selecting the best columns for CO2 prediction
    # Engine Size, Cylinders, and Combined Fuel (L/100km)
    X_co2 = df_co2[['Engine Size(L)', 'Cylinders', 'Fuel Consumption Comb (L/100 km)']]
    y_co2 = df_co2['CO2 Emissions(g/km)']
    
    model_co2 = RandomForestRegressor(n_estimators=100, random_state=42)
    model_co2.fit(X_co2, y_co2)
    
    # Save the model
    co2_path = os.path.join(BACKEND_ML_DIR, "co2_model.joblib")
    joblib.dump(model_co2, co2_path)
    print(f"✅ CO2 Model Saved to {co2_path}")

    # --- PART 2: TRAFFIC IMPACT MODEL ---
    print("\n🚦 Training Traffic Congestion Model...")
    df_traffic = pd.read_csv(TRAFFIC_FILE)
    
    # Feature Engineering for Traffic
    # We want to predict traffic_volume based on weather and time
    df_traffic['date_time'] = pd.to_datetime(df_traffic['date_time'])
    df_traffic['hour'] = df_traffic['date_time'].dt.hour
    df_traffic['day_of_week'] = df_traffic['date_time'].dt.dayofweek
    
    # Encode categorical weather
    le_weather = LabelEncoder()
    df_traffic['weather_encoded'] = le_weather.fit_transform(df_traffic['weather_main'])
    
    # Save the encoder (needed for inference)
    le_path = os.path.join(BACKEND_ML_DIR, "weather_encoder.joblib")
    joblib.dump(le_weather, le_path)

    # Features: hour, day_of_week, temp, weather_encoded
    # Target: traffic_volume
    features_traffic = ['hour', 'day_of_week', 'temp', 'weather_encoded']
    X_traffic = df_traffic[features_traffic]
    y_traffic = df_traffic['traffic_volume']
    
    # Use Gradient Boosting for better time-series pattern recognition
    model_traffic = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model_traffic.fit(X_traffic, y_traffic)
    
    # Save Traffic Model
    traffic_path = os.path.join(BACKEND_ML_DIR, "traffic_model.joblib")
    joblib.dump(model_traffic, traffic_path)
    print(f"✅ Traffic Model Saved to {traffic_path}")

    print("\n✨ Unified ML Integration Complete! All models are trained and ready.")

if __name__ == "__main__":
    train_unified_ml()
