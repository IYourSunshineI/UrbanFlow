# 1. READ CONFIG: Define your LocalStack bucket (must match main.tf)
$BUCKET_NAME = "urban-flow-frontend-local"
$PROFILE = "localstack" # Ensure you have 'aws configure --profile localstack' set up or use env vars

Write-Host "Starting LocalStack 'Amplify' Build Pipeline..."

# 2. PRE-BUILD (Mimics amplify.yml 'preBuild')
Write-Host "Installing dependencies..."
npm ci

# 3. BUILD (Mimics amplify.yml 'build')
Write-Host "Building Angular App..."
npm run build --configuration development

# 4. PARSE ARTIFACT PATH (Manual or grep from amplify.yml)
$BUILD_DIR = "dist/urban-flow-frontend/browser"

# 5. DEPLOY (Mimics the Amplify 'Publish' phase)
Write-Host "Deploying to LocalStack S3..."
# Using awslocal is easiest, or use standard aws cli with endpoint-url
awslocal s3 sync "./$BUILD_DIR" "s3://$BUCKET_NAME" --delete --cache-control "max-age=0,no-cache,no-store,must-revalidate"

Write-Host "Deployed! Access your app here:"
Write-Host "http://$BUCKET_NAME.s3-website.localhost.localstack.cloud:4566"
