import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sys
import pandas as pd
import yaml
import json
import mlflow
import mlflow.sklearn
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def train_model(train_file, model_path, scaler_path):
    
    # Load Params
    params = load_params()
    train_params = params["train"]
    mlflow_params = params["mlflow"]

    print("Starting Model Training...")

    mlflow.set_experiment(mlflow_params["experiment_name"])
    with mlflow.start_run():
        # Prepare Data
        df = pd.read_csv(train_file)
        X_train = df.drop("species", axis=1)
        y_train = df['species']

        scaler = StandardScaler()

        X_train_scaled = scaler.fit_transform(X_train)

        # Prepare Model
        if train_params["algorithm"] == "random_forest":
            model = RandomForestClassifier(**train_params["hyperparameters"])
        else:
            raise ValueError(f"Unknown Model Algorithm: {train_params['algorithm']}")
        
        # Train Model
        model.fit(X_train_scaled, y_train)

        # Calculate Training metrics
        y_pred_train = model.predict(X_train_scaled)
        train_accuracy = accuracy_score(y_train, y_pred_train)

        # Track Experiment Using MLflow
        mlflow.log_params(train_params["hyperparameters"])
        mlflow.log_metric("Train-Accuracy", train_accuracy)
        mlflow.sklearn.log_model(model, "model")

        # Save Metrics
        metrics = {
            "algorithm": train_params["algorithm"],
            "accuracy": train_accuracy,
            "n_samples": len(X_train_scaled)
        }

        if not os.path.exists("metrics"):
            os.makedirs("metrics")


        with open("metrics/train_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        # Save Model and Scaler

        if not os.path.exists("models"):
            os.makedirs("models")

        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)

        print(f"Model trained with {train_params['algorithm']}")
        print(f"Training accuracy: {train_accuracy:.4f}")
        print(f"Model saved to: {model_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python src/train_model.py <train_file> <model_file> <scaler_file>")
        sys.exit(1)
    
    train_file = sys.argv[1]
    model_file = sys.argv[2]
    scaler_file = sys.argv[3]
    
    train_model(train_file, model_file, scaler_file)