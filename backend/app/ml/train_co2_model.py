import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

# 1. Load Data
# Note: Adjust path to your absolute CSV location
DATA_PATH = r"d:\EcoRoute-AI\ml\CO2 Emissions_Canada.csv"
MODEL_SAVE_PATH = r"d:\EcoRoute-AI\backend\app\ml\co2_model.joblib"

def train_model():
    print("🚀 Starting ML Model Training...")
    
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Data file not found at {DATA_PATH}")
        return

    # Load the dataset
    df = pd.read_csv(DATA_PATH)
    
    # Feature selection
    # We'll use these features to predict CO2
    features = ['Engine Size(L)', 'Cylinders', 'Fuel Consumption Comb (L/100 km)']
    target = 'CO2 Emissions(g/km)'
    
    X = df[features]
    y = df[target]
    
    # Split data (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"📊 Training on {len(X_train)} samples...")
    
    # Initialize and train the model
    # Random Forest is powerful and handles non-linear relationships well
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    score = model.score(X_test, y_test)
    print(f"✅ Training Complete! Model Accuracy (R² Score): {score:.4f}")
    
    # Save the model to a file
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"💾 Model saved to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_model()
