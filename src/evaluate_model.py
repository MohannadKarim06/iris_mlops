import sys 
import joblib
import json
import pandas as pd
import mlflow
from sklearn.metrics import accuracy_score, precision_score, f1_score, recall_score, classification_report
import yaml


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def evaluate_model(model_file, scaler_file, test_file):

    # Load Params
    params = load_params()
    eval_params = params['evaluate']
    mlflow_params = params['mlflow']

    # Track Using MLflow
    mlflow.set_experiment(mlflow_params['experiment_name'])

    # Prepare Data
    df = pd.read_csv(test_file)
    X_test = df.drop("species", axis=1)
    y_test = df['species']

    scaler = joblib.load(scaler_file)

    X_scaled_test = scaler.transform(X_test)

    model = joblib.load(model_file)

    with mlflow.start_run():

        # Evaluate Model Performance
        y_pred = model.predict(X_scaled_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')

        # Save and Track Evaluation Metrics
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'n_test_samples': len(X_test),
            'meets_threshold': accuracy >= eval_params['performance_threshold']
        }
        mlflow.log_metrics(metrics)

        with open("metrics/eval_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        print("Model Evaluation Results:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1:.4f}")
        print(f"Performance threshold met: {accuracy >= eval_params['performance_threshold']}")
        
        print("\nDetailed Classification Report:")
        print(classification_report(y_test, y_pred))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python src/evaluate_model.py <model_file> <scaler_file> <test_file>")
        sys.exit(1)
    
    model_file = sys.argv[1]
    scaler_file = sys.argv[2]
    test_file = sys.argv[3]
    
    evaluate_model(model_file, scaler_file, test_file)


