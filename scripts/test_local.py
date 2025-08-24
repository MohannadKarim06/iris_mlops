import requests
import json

# Test the BentoML service locally
BASE_URL = "http://localhost:3000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())

def test_single_prediction():
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }
    response = requests.post(f"{BASE_URL}/predict_single", json=payload)
    print("Single Prediction:", response.text)

def test_batch_prediction():
    payload = {
        "features": [
            {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
            {"sepal_length": 6.2, "sepal_width": 2.9, "petal_length": 4.3, "petal_width": 1.3}
        ]
    }
    response = requests.post(f"{BASE_URL}/predict_batch", json=payload)
    print("Batch Prediction:", response.json())

if __name__ == "__main__":
    test_health()
    test_single_prediction()
    test_batch_prediction()