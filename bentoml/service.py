import bentoml
import numpy as np
import pandas as pd
from bentoml.io import JSON, Text
from pydantic import BaseModel
from typing import List
import joblib
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from prometheus_client import Counter, Histogram, Gauge
import os

# Prometheus metrics
PREDICTION_COUNTER = Counter('predictions_total', 'Total predictions made', ['model_version'])
PREDICTION_LATENCY = Histogram('prediction_duration_seconds', 'Prediction latency')
DRIFT_SCORE = Gauge('feature_drift_score', 'Feature drift detection score')
CIRCUIT_BREAKER = Gauge('circuit_breaker_open', 'Circuit breaker status')

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

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

# Load model artifacts
model_ref = bentoml.sklearn.get("iris_classifier:latest")
iris_service = bentoml.Service("iris_classifier", runners=[model_ref.to_runner()])

@iris_service.api(input=JSON(pydantic_model=IrisFeatures), output=Text())
@limiter.limit("30/minute")  # Rate limiting
def predict_single(features: IrisFeatures) -> str:
    """Single prediction with circuit breaker and monitoring"""
    start_time = time.time()
    
    try:
        # Circuit breaker check
        if is_circuit_open():
            CIRCUIT_BREAKER.set(1)
            return "Service temporarily unavailable"
        
        # Feature drift detection (simple baseline comparison)
        drift_score = calculate_drift(features)
        DRIFT_SCORE.set(drift_score)
        
        # Make prediction
        input_data = np.array([[
            features.sepal_length, features.sepal_width,
            features.petal_length, features.petal_width
        ]])
        
        result = iris_service.runners[0].predict.run(input_data)
        
        # Success - reset circuit breaker
        circuit_state["failures"] = 0
        CIRCUIT_BREAKER.set(0)
        
        # Record metrics
        PREDICTION_COUNTER.labels(model_version="v1.0").inc()
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return f"Predicted species: {result[0]}"
        
    except Exception as e:
        # Handle failure for circuit breaker
        handle_failure()
        logging.error(f"Prediction failed: {str(e)}")
        return "Prediction failed"

@iris_service.api(input=JSON(pydantic_model=IrisBatch), output=JSON())
@limiter.limit("10/minute")
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
            result = iris_service.runners[0].predict.run(input_data)
            predictions.append(result[0])
        
        PREDICTION_COUNTER.labels(model_version="v1.0").inc(len(predictions))
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return {"predictions": predictions, "count": len(predictions)}
        
    except Exception as e:
        handle_failure()
        return {"error": str(e)}

def is_circuit_open():
    """Check if circuit breaker is open"""
    if circuit_state["failures"] >= MAX_FAILURES:
        if time.time() - circuit_state["last_failure"] < RECOVERY_TIMEOUT:
            return True
        else:
            # Reset circuit breaker after timeout
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
    """Simple drift detection - compare with baseline sample"""
    baseline = {"sepal_length": 5.8, "sepal_width": 3.0, "petal_length": 3.7, "petal_width": 1.2}
    
    drift_score = abs(features.sepal_length - baseline["sepal_length"]) + \
                  abs(features.sepal_width - baseline["sepal_width"]) + \
                  abs(features.petal_length - baseline["petal_length"]) + \
                  abs(features.petal_width - baseline["petal_width"])
    
    return drift_score / 4  # Normalize

# Add rate limit handler
iris_service.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)