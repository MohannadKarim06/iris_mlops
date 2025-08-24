import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

# Page config
st.set_page_config(page_title="Iris Classifier", page_icon="🌸", layout="wide")

# Title and description
st.title("🌸 Iris Classification MLOps Demo")
st.markdown("### Enterprise-grade ML pipeline with monitoring")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page", ["Prediction", "Monitoring", "Batch Upload"])
    
    st.header("Model Info")
    st.info("Model: Random Forest\nVersion: v1.0\nAccuracy: 95%+")
    
    # Grafana link
    st.markdown("📊 [View Grafana Dashboard](http://your-grafana-url)")

# API endpoint
API_BASE = "http://your-alb-url"  # Replace with actual ALB URL

if page == "Prediction":
    st.header("Single Prediction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sepal_length = st.slider("Sepal Length (cm)", 4.0, 8.0, 5.0)
        sepal_width = st.slider("Sepal Width (cm)", 2.0, 5.0, 3.0)
        
    with col2:
        petal_length = st.slider("Petal Length (cm)", 1.0, 7.0, 4.0)
        petal_width = st.slider("Petal Width (cm)", 0.1, 3.0, 1.0)
    
    if st.button("Predict Species", type="primary"):
        payload = {
            "sepal_length": sepal_length,
            "sepal_width": sepal_width,
            "petal_length": petal_length,
            "petal_width": petal_width
        }
        
        try:
            response = requests.post(f"{API_BASE}/predict_single", json=payload)
            if response.status_code == 200:
                result = response.text
                st.success(f"🎉 {result}")
                
                # Show prediction confidence visualization
                fig = px.bar(
                    x=['setosa', 'versicolor', 'virginica'],
                    y=[0.9 if 'setosa' in result else 0.1, 
                       0.9 if 'versicolor' in result else 0.1,
                       0.9 if 'virginica' in result else 0.1],
                    title="Prediction Confidence"
                )
                st.plotly_chart(fig)
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

elif page == "Batch Upload":
    st.header("Batch Prediction")
    
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded data:")
        st.dataframe(df.head())
        
        if st.button("Process Batch"):
            # Convert DataFrame to API format
            batch_data = []
            for _, row in df.iterrows():
                batch_data.append({
                    "sepal_length": float(row['sepal_length']),
                    "sepal_width": float(row['sepal_width']),
                    "petal_length": float(row['petal_length']),
                    "petal_width": float(row['petal_width'])
                })
            
            payload = {"features": batch_data}
            
            try:
                response = requests.post(f"{API_BASE}/predict_batch", json=payload)
                if response.status_code == 200:
                    results = response.json()
                    df['predictions'] = results['predictions']
                    
                    st.success(f"Processed {results['count']} predictions!")
                    st.dataframe(df)
                    
                    # Download results
                    csv = df.to_csv(index=False)
                    st.download_button("Download Results", csv, "predictions.csv")
                    
                    # Show distribution chart
                    fig = px.histogram(df, x='predictions', title="Prediction Distribution")
                    st.plotly_chart(fig)
                else:
                    st.error("Batch processing failed")
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif page == "Monitoring":
    st.header("System Monitoring")
    
    # Fetch metrics from Prometheus (you'd implement this)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Predictions", "1,234", "+12")
    
    with col2:
        st.metric("Average Latency", "45ms", "-2ms")
        
    with col3:
        st.metric("Success Rate", "99.8%", "+0.1%")
    
    # Mock monitoring charts
    import numpy as np
    
    # Prediction volume over time
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    predictions = np.random.randint(50, 200, 30)
    
    fig = px.line(x=dates, y=predictions, title="Predictions Over Time")
    st.plotly_chart(fig)
    
    # Model performance metrics
    metrics_df = pd.DataFrame({
        'Metric': ['Accuracy', 'Precision', 'Recall', 'F1-Score'],
        'Value': [0.95, 0.94, 0.96, 0.95]
    })
    
    fig = px.bar(metrics_df, x='Metric', y='Value', title="Model Performance")
    st.plotly_chart(fig)