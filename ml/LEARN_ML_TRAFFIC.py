"""
Challenge: Traffic Prediction Model
This is a starter script for you to build a Traffic Flow Predictor 
using your 'traffic_weather_full2020.csv' data!
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
import joblib

def teach_traffic_ml():
    # 1. Load your traffic and weather data
    DATA_PATH = r"d:\EcoRoute-AI\ml\traffic_weather_full2020.csv"
    
    print("🚦 Loading your traffic data for analysis...")
    df = pd.read_csv(DATA_PATH)
    
    # Let's see what we can predict
    print("Columns available:", df.columns.tolist())
    
    # Tip: You can predict 'Flow' (how many cars) based on 'Weather' conditions.
    # We would need to convert 'Weather' (text like 'Fair') into numbers first!
    
    """
    To-Do for you:
    1. Preprocess the time column to get 'Hour of day'.
    2. Convert categorical weather to numeric using pd.get_dummies().
    3. Train a model to predict 'Flow'.
    4. Save it as 'traffic_model.joblib'.
    """
    
    print("\n💡 Tip: Machine Learning loves numbers. Always convert text categories to numbers before training!")

if __name__ == "__main__":
    teach_traffic_ml()
