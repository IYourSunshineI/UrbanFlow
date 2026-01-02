#!/bin/bash

# 1. READ CONFIG: Define your LocalStack bucket (must match main.tf)
BUCKET_NAME="urban-flow-frontend-local"
PROFILE="localstack" # Ensure you have 'aws configure --profile localstack' set up or use env vars

echo "🚀 Starting LocalStack 'Amplify' Build Pipeline..."

# 2. PRE-BUILD (Mimics amplify.yml 'preBuild')
echo "📦 Installing dependencies..."
npm ci

# 3. BUILD (Mimics amplify.yml 'build')
echo "🛠  Building Angular App..."
npm run build --configuration development

# 4. PARSE ARTIFACT PATH (Manual or grep from amplify.yml)
# In a real fancy setup, you could use 'yq' to read this from amplify.yml directly:
# BUILD_DIR=$(yq '.frontend.artifacts.baseDirectory' amplify.yml)
BUILD_DIR="dist/urban-flow-frontend/browser" 

# 5. DEPLOY (Mimics the Amplify 'Publish' phase)
echo "☁️  Deploying to LocalStack S3..."
# Using awslocal is easiest, or use standard aws cli with endpoint-url
awslocal s3 sync ./$BUILD_DIR s3://$BUCKET_NAME \
  --delete \
  --cache-control "max-age=0,no-cache,no-store,must-revalidate" # Disable caching for local dev

echo "✅ Deployed! Access your app here:"
echo "http://$BUCKET_NAME.s3-website.localhost.localstack.cloud:4566"