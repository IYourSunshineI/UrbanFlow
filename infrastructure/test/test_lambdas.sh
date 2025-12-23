#!/bin/bash

# Get API ID from Terraform output
cd terraform
API_ID=$(terraform output -raw api_id)
STREAM_NAME="urbanflow-input-stream"
cd ..

# Construct URL for API Gateway V1 (REST API)
# Typically: http://localhost:4566/restapis/<api_id>/<stage_name>/_user_request_/<resource_path>
# Or simpler LocalStack format: http://localhost:4566/_aws/execute-api/<api_id>/<stage_name>
LOCAL_API_URL="http://localhost:4566/_aws/execute-api/$API_ID/dev"

echo "Testing UrbanFlow Lambdas..."
echo "API ID: $API_ID"
echo "Constructed URL: $LOCAL_API_URL"
echo "Stream Name: $STREAM_NAME"
echo ""

# 1. Test Ingestion Processor (via Kinesis)
echo "Testing Kinesis Trigger (IngestionProcessor)..."
# Create base64 encoded payload
PAYLOAD=$(echo -n '{"sensorId": "123", "traffic": 50}' | base64)
# # Send record to Kinesis using curl (Kinesis API)
# API Target for PutRecord: Kinesis_20131202.PutRecord
# Endpoint: http://localhost:4566
echo "Sending record to Kinesis stream '$STREAM_NAME'..."
echo ""

curl -s -X POST "http://localhost:4566" \
  -H "Content-Type: application/x-amz-json-1.1" \
  -H "X-Amz-Target: Kinesis_20131202.PutRecord" \
  -d "{
    \"StreamName\": \"$STREAM_NAME\",
    \"PartitionKey\": \"123\",
    \"Data\": \"$PAYLOAD\"
  }"
echo "Record sent to Kinesis. Check LocalStack logs for 'Hello from UrbanFlowIngestionProcessor!'"
echo ""

# 2. Test Data Reader (via API Gateway)
echo "Testing API Gateway (DataReader)..."
# Make GET request to the API
RESPONSE=$(curl -s "$LOCAL_API_URL/traffic")
echo "Response from API:"
# Attempt to format JSON if available, otherwise just print
if command -v jq &> /dev/null; then
    echo "$RESPONSE" | jq .
else
    echo "$RESPONSE"
fi

echo ""
echo "Verification Complete!"
