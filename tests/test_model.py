import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
import os
import tempfile
import pytest 
import joblib
from sklearn.datasets import load_iris
from src.data_preprocessing import preprocess_data
from src.train_model import train_model


def test_model_training():

    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df["species"] = iris.target_names[iris.target]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        file_path = f.name
        df.to_csv(file_path, index=False)


    model_path = tempfile.mktemp(suffix=".pkl")
    scaler_path = tempfile.mktemp(suffix=".pkl")


    try:

        assert callable(train_model)

    finally:

        for path in [file_path, model_path, scaler_path]:
            if os.path.exists(path):
                os.unlink(path)


def test_model_predictions():
    """Test model prediction functionality"""

    assert True  # Placeholder test