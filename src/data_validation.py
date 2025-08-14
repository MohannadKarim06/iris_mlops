import pandas as pd
import numpy as np
import json
import sys

def validate_data_schema(df, expected_columns):
    """Validate data schema"""
    missing_cols = set(expected_columns) - set(df.columns)
    extra_cols = set(df.columns) - set(expected_columns)
    
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    if extra_cols:
        print(f"Warning: Extra columns found: {extra_cols}")
    
    return True

def validate_data_quality(df):
    """Check data quality"""
    issues = []
    
    # Check for missing values
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        issues.append(f"Missing values: {missing_count}")
    
    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        issues.append(f"Duplicate rows: {duplicate_count}")
    
    # Check target distribution
    if 'species' in df.columns:
        species_counts = df['species'].value_counts()
        min_samples = species_counts.min()
        if min_samples < 10:
            issues.append(f"Low sample count for some species: min={min_samples}")
    
    return issues

def validate_iris_data():
    """Validate Iris dataset"""
    try:
        # Load data
        df = pd.read_csv('data/processed/train.csv')
        
        # Expected schema for Iris dataset
        expected_columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']
        
        # Schema validation
        validate_data_schema(df, expected_columns)
        
        # Quality validation
        quality_issues = validate_data_quality(df)
        
        if quality_issues:
            print("Data quality issues found:")
            for issue in quality_issues:
                print(f"  - {issue}")
            return False
        else:
            print("Data validation passed!")
            return True
            
    except Exception as e:
        print(f"Data validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = validate_iris_data()
    if not success:
        sys.exit(1)