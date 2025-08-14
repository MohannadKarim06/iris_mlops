import json
import sys

def check_performance_threshold():
    """Check if model meets performance threshold"""
    try:
        with open('metrics/eval_metrics.json', 'r') as f:
            metrics = json.load(f)
        
        accuracy = metrics['accuracy']
        threshold = 0.90  # From params.yaml
        
        meets_threshold = accuracy >= threshold
        
        print(f"Model accuracy: {accuracy:.4f}")
        print(f"Threshold: {threshold}")
        print(f"Meets threshold: {meets_threshold}")
        
        if meets_threshold:
            print("MODEL_APPROVED=true")
            return True
        else:
            print("MODEL_APPROVED=false")
            return False
            
    except Exception as e:
        print(f"Error checking performance: {e}")
        return False

if __name__ == "__main__":
    success = check_performance_threshold()
    sys.exit(0 if success else 1)