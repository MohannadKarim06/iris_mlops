import pandas as pd
import yaml 
import os


def load_params():
    with open("params.yaml", "r") as f:
        return yaml.safe_load(f)
    

def ingest_data():
    
    # Load Params
    params = load_params()
    dataset_url = params["data_ingestion"]["dataset_url"]
    raw_dataset_path = params["data_ingestion"]["dataset_path"]

    print("Starting Data Ingestion Stage...")

    # Make Dir If Doesn't Exist
    os.makedirs(os.path.dirname(raw_dataset_path), exist_ok=True)

    # Download Dataset
    df = pd.read_csv(dataset_url)

    # Save Dataset
    df.to_csv(raw_dataset_path, index=False)

    print(f"Data Ingestion Successful Dataset Contains {len(df)} rows and {list(df.columns)} as Columns.")
    print(f"Species distribution:\n{df['species'].value_counts()}")


if __name__ == "__main__":
    ingest_data()
