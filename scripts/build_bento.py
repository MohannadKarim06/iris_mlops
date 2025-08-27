import bentoml
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os
import sys

def build_bento_service():
    """Build BentoML service with trained model"""
    
    try:
        print("🔧 Starting BentoML service build...")
        
        # Check if model files exist
        model_path = 'models/model.pkl'
        scaler_path = 'models/scaler.pkl'
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler file not found: {scaler_path}")
        
        # Load trained model and scaler
        print("Loading model and scaler...")
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        print(f"Model type: {type(model)}")
        print(f"Scaler type: {type(scaler)}")
        
        # Save model to BentoML store
        print("Saving model to BentoML store...")
        model_tag = bentoml.sklearn.save_model(
            name="iris_classifier",
            model=model,
            labels={
                "accuracy": "0.95+",
                "framework": "sklearn",
                "algorithm": "RandomForest",
                "version": "v1.0"
            },
            metadata={
                "accuracy": "0.95+",
                "framework": "sklearn",
                "algorithm": "RandomForest"
            }
        )
        
        # Save scaler separately
        print("Saving scaler to BentoML store...")
        scaler_tag = bentoml.sklearn.save_model(
            name="iris_scaler", 
            model=scaler,
            labels={
                "type": "StandardScaler",
                "version": "v1.0"
            },
            metadata={"type": "StandardScaler"}
        )
        
        print(f"Model saved: {model_tag}")
        print(f"Scaler saved: {scaler_tag}")
        
        # List saved models for verification
        print("\nAvailable models in BentoML store:")
        try:
            models = bentoml.models.list()
            for model in models:
                print(f"  - {model.tag}: {model.info.labels}")
        except Exception as e:
            print(f"Warning: Could not list models - {e}")
        
        print("🎉 BentoML service build completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error building BentoML service: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = build_bento_service()
    if not success:
        sys.exit(1)
