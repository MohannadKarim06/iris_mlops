import bentoml
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os

def build_bento_service():
    """Build BentoML service with trained model"""
    
    # Load trained model and scaler
    model = joblib.load('models/model.pkl')
    scaler = joblib.load('models/scaler.pkl')
    
    # Save model to BentoML store
    model_tag = bentoml.sklearn.save_model(
        name="iris_classifier",
        model=model,
        metadata={
            "accuracy": "0.95+",
            "framework": "sklearn",
            "algorithm": "RandomForest"
        }
    )
    
    # Save scaler separately (BentoML doesn't handle this automatically)
    scaler_tag = bentoml.sklearn.save_model(
        name="iris_scaler", 
        model=scaler,
        metadata={"type": "StandardScaler"}
    )
    
    print(f"Model saved: {model_tag}")
    print(f"Scaler saved: {scaler_tag}")
        

if __name__ == "__main__":
    build_bento_service()
