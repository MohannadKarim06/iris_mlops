import pytest
import pandas as pd
from src.data_validation import validate_data_schema, validate_data_quality

def test_data_schema_validation():
    """Test data schema validation"""
    # Create sample data
    df = pd.DataFrame({
        'sepal_length': [5.1, 4.9, 4.7],
        'sepal_width': [3.5, 3.0, 3.2],
        'petal_length': [1.4, 1.4, 1.3],
        'petal_width': [0.2, 0.2, 0.2],
        'species': ['setosa', 'setosa', 'setosa']
    })
    
    expected_columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']
    
    # Should pass
    assert validate_data_schema(df, expected_columns) == True

def test_data_quality_validation():
    """Test data quality validation"""
    # Create clean data
    df = pd.DataFrame({
        'sepal_length': [5.1, 4.9, 4.7],
        'sepal_width': [3.5, 3.0, 3.2],
        'petal_length': [1.4, 1.4, 1.3],
        'petal_width': [0.2, 0.2, 0.2],
        'species': ['setosa', 'setosa', 'setosa']
    })
    
    issues = validate_data_quality(df)
    assert len(issues) == 0  # No issues expected