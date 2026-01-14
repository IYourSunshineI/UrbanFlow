import boto3
import os
import mimetypes

# Configuration
BUCKET_NAME = "urban-flow-frontend-local"
BUILD_DIR = "dist/urban-flow-frontend/browser"
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"

def deploy():
    # Initialize S3 client for Localstack
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

    print(f"🚀 Deploying to bucket: {BUCKET_NAME}")

    # Check if bucket exists
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except Exception:
        print(f"❌ Bucket {BUCKET_NAME} does not exist!")
        return

    # Walk through the build directory
    for root, dirs, files in os.walk(BUILD_DIR):
        for file in files:
            local_path = os.path.join(root, file)
            # Calculate relative path for S3 key
            relative_path = os.path.relpath(local_path, BUILD_DIR)
            s3_key = relative_path.replace("\\", "/") # Ensure forward slashes

            # Guess MIME type
            content_type, _ = mimetypes.guess_type(local_path)
            if not content_type:
                content_type = "application/octet-stream"

            print(f"Uploading {s3_key} ({content_type})...")
            
            s3.upload_file(
                local_path, 
                BUCKET_NAME, 
                s3_key, 
                ExtraArgs={'ContentType': content_type, 'CacheControl': 'max-age=0,no-cache,no-store,must-revalidate'}
            )

    print("✅ Deployment complete!")

if __name__ == "__main__":
    deploy()
