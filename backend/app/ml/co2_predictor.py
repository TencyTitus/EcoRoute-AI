import joblib
import os
import pandas as pd
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(__file__)
CO2_MODEL_PATH = os.path.join(BASE_DIR, "co2_model.joblib")
TRAFFIC_MODEL_PATH = os.path.join(BASE_DIR, "traffic_model.joblib")
WEATHER_ENCODER_PATH = os.path.join(BASE_DIR, "weather_encoder.joblib")

class UnifiedPredictor:
    def __init__(self):
        self.co2_model = None
        self.traffic_model = None
        self.weather_encoder = None
        self._load_models()

    def _load_models(self):
        try:
            if os.path.exists(CO2_MODEL_PATH):
                self.co2_model = joblib.load(CO2_MODEL_PATH)
            if os.path.exists(TRAFFIC_MODEL_PATH):
                self.traffic_model = joblib.load(TRAFFIC_MODEL_PATH)
            if os.path.exists(WEATHER_ENCODER_PATH):
                self.weather_encoder = joblib.load(WEATHER_ENCODER_PATH)
            print("🧠 Unified ML Intelligence Engine loaded")
        except Exception as e:
            print(f"❌ Error loading models: {e}")

    def predict_co2(self, engine_size, cylinders, fuel_kmpl):
        """Predicts CO2 (g/km) using the Vehicle Model"""
        if self.co2_model is None:
            return fuel_kmpl * 23.5 # Fallback
            
        fuel_l100 = 100 / fuel_kmpl if fuel_kmpl > 0 else 10.0
        data = pd.DataFrame([[engine_size, cylinders, fuel_l100]], 
                           columns=['Engine Size(L)', 'Cylinders', 'Fuel Consumption Comb (L/100 km)'])
        return float(self.co2_model.predict(data)[0])

    def predict_traffic_impact(self, hour: int = None, day: int = None, temp: float = 290.0, weather: str = "Clear"):
        """
        Predicts traffic volume using the Environmental Model.
        Returns an 'Impact Factor' (1.0 = normal, 2.0 = heavy congestion).
        """
        if self.traffic_model is None:
            return 1.0 # Default
            
        now = datetime.now()
        h = hour if hour is not None else now.hour
        d = day if day is not None else now.weekday()
        
        try:
            w_encoded = self.weather_encoder.transform([weather])[0]
        except:
            w_encoded = 0 # Default if weather string is unknown
            
        data = pd.DataFrame([[h, d, temp, w_encoded]], 
                           columns=['hour', 'day_of_week', 'temp', 'weather_encoded'])
        
        predicted_volume = float(self.traffic_model.predict(data)[0])
        
        # Normalize volume to an impact factor (Max volume in city is usually ~5000-6000)
        # 1.0 factor = low traffic
        # 1.5 - 2.0 = heavy traffic
        factor = 1.0 + (predicted_volume / 6000.0) 
        return round(factor, 2)

# Global instance for the app
predictor = UnifiedPredictor()
