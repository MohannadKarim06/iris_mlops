import boto3
import json
from botocore.exceptions import ClientError

def setup_s3_bucket(bucket_name, region='us-west-2'):
    """Create S3 bucket for DVC remote storage"""
    s3_client = boto3.client('s3', region_name=region)
    
    try:
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        
        print(f"S3 bucket '{bucket_name}' created successfully")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"Bucket '{bucket_name}' already exists")
            return True
        else:
            print(f"Error creating bucket: {e}")
            return False

if __name__ == "__main__":
    bucket_name = "my-iris-mlops-data"  # Change this to your unique bucket name
    setup_s3_bucket(bucket_name)