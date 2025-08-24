import bentoml
import numpy as np
import pandas as pd
from bentoml.io import JSON, Text
from pydantic import BaseModel
from typing import List
import logging
import time
from prometheus_client import Counter, Histogram, Gauge

# Prometheus metrics
PREDICTION_COUNTER = Counter('predictions_total', 'Total predictions made', ['model_version'])
PREDICTION_LATENCY = Histogram('prediction_duration_seconds', 'Prediction latency')
DRIFT_SCORE = Gauge('feature_drift_score', 'Feature drift detection score')
CIRCUIT_BREAKER = Gauge('circuit_breaker_open', 'Circuit breaker status')

# Circuit breaker state
circuit_state = {"failures": 0, "last_failure": 0, "is_open": False}
MAX_FAILURES = 3
RECOVERY_TIMEOUT = 60

class IrisFeatures(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

class IrisBatch(BaseModel):
    features: List[IrisFeatures]

# Load model and scaler from BentoML store
model_runner = bentoml.sklearn.get("iris_classifier:latest").to_runner()
scaler_runner = bentoml.sklearn.get("iris_scaler:latest").to_runner()

# Create service
iris_service = bentoml.Service("iris_classifier", runners=[model_runner, scaler_runner])

@iris_service.api(input=JSON(pydantic_model=IrisFeatures), output=Text())
def predict_single(features: IrisFeatures) -> str:
    """Single prediction with circuit breaker and monitoring"""
    start_time = time.time()
    
    try:
        # Circuit breaker check
        if is_circuit_open():
            CIRCUIT_BREAKER.set(1)
            return "Service temporarily unavailable"
        
        # Feature drift detection
        drift_score = calculate_drift(features)
        DRIFT_SCORE.set(drift_score)
        
        # Prepare input data
        input_data = np.array([[
            features.sepal_length, features.sepal_width,
            features.petal_length, features.petal_width
        ]])
        
        # Scale features
        scaled_data = scaler_runner.transform.run(input_data)
        
        # Make prediction
        result = model_runner.predict.run(scaled_data)
        
        # Success - reset circuit breaker
        circuit_state["failures"] = 0
        CIRCUIT_BREAKER.set(0)
        
        # Record metrics
        PREDICTION_COUNTER.labels(model_version="v1.0").inc()
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return f"Predicted species: {result[0]}"
        
    except Exception as e:
        handle_failure()
        logging.error(f"Prediction failed: {str(e)}")
        return "Prediction failed"

@iris_service.api(input=JSON(pydantic_model=IrisBatch), output=JSON())
def predict_batch(batch: IrisBatch) -> dict:
    """Batch prediction"""
    start_time = time.time()
    
    try:
        if is_circuit_open():
            return {"error": "Service temporarily unavailable"}
            
        predictions = []
        for features in batch.features:
            input_data = np.array([[
                features.sepal_length, features.sepal_width,
                features.petal_length, features.petal_width
            ]])
            scaled_data = scaler_runner.transform.run(input_data)
            result = model_runner.predict.run(scaled_data)
            predictions.append(result[0])
        
        PREDICTION_COUNTER.labels(model_version="v1.0").inc(len(predictions))
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return {"predictions": predictions, "count": len(predictions)}
        
    except Exception as e:
        handle_failure()
        return {"error": str(e)}

@iris_service.api(input=Text(), output=JSON())
def health() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": True,
        "circuit_breaker": "open" if is_circuit_open() else "closed"
    }

def is_circuit_open():
    """Check if circuit breaker is open"""
    if circuit_state["failures"] >= MAX_FAILURES:
        if time.time() - circuit_state["last_failure"] < RECOVERY_TIMEOUT:
            return True
        else:
            circuit_state["failures"] = 0
            return False
    return False

def handle_failure():
    """Handle service failure for circuit breaker"""
    circuit_state["failures"] += 1
    circuit_state["last_failure"] = time.time()
    if circuit_state["failures"] >= MAX_FAILURES:
        CIRCUIT_BREAKER.set(1)

def calculate_drift(features: IrisFeatures):
    """Simple drift detection"""
    baseline = {"sepal_length": 5.8, "sepal_width": 3.0, "petal_length": 3.7, "petal_width": 1.2}
    
    drift_score = (abs(features.sepal_length - baseline["sepal_length"]) + 
                  abs(features.sepal_width - baseline["sepal_width"]) + 
                  abs(features.petal_length - baseline["petal_length"]) + 
                  abs(features.petal_width - baseline["petal_width"])) / 4
    
    return drift_score