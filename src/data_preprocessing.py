import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import yaml 
import sys
from sklearn.model_selection import train_test_split


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)


def preprocess_data(input_file, train_path, test_path):

    params = load_params()
    preprocessing_params = params["data_preprocessing"]

    print("Starting Data Preprocessing...")

    # Load Dataset
    df = pd.read_csv(input_file)

    # Basic Dataset Cleaning
    df = df.dropna()
    df = df.drop_duplicates()

    # Split Data and Target
    X = df.drop("species", axis=1)
    y = df["species"]

    # Perform Train-Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=preprocessing_params["test_size"],
        random_state=preprocessing_params["random_state"],
        stratify=y
    )

    # Define Train Test split
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)

    # Save Train Test split
    if not os.path.exists(train_path):
        os.makedirs(train_path)

    if not os.path.exists(train_path):
        os.makedirs(train_path)

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"Data preprocessed:")
    print(f"Training set: {len(train_df)} samples")
    print(f"Test set: {len(test_df)} samples")
    print(f"Features: {list(X.columns)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python src/data_preprocessing.py <input_file> <train_file> <test_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    train_path = sys.argv[2]
    test_path = sys.argv[3]

    preprocess_data(input_file, train_path, test_path)