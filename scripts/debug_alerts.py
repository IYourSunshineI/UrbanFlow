import boto3
import time
from datetime import datetime

# Configure boto3 for Localstack
localstack_endpoint = 'http://localhost:4566'
region = 'us-east-1'
creds = {'aws_access_key_id': 'test', 'aws_secret_access_key': 'test'}

logs = boto3.client('logs', endpoint_url=localstack_endpoint, region_name=region, **creds)
dynamodb = boto3.resource('dynamodb', endpoint_url=localstack_endpoint, region_name=region, **creds)

def inspect_logs(log_group_name):
    print(f"\n--- Logs for {log_group_name} ---")
    try:
        response = logs.filter_log_events(
            logGroupName=log_group_name,
            startTime=int((time.time() - 3600) * 1000) # Last hour
        )
        events = response.get('events', [])
        if not events:
            print("No log events found.")
        for event in events:
            print(f"[{datetime.fromtimestamp(event['timestamp']/1000)}] {event['message'].strip()}")
    except Exception as e:
        print(f"Error fetching logs: {e}")

def scan_table(table_name):
    print(f"\n--- Scan Table: {table_name} ---")
    try:
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response.get('Items', [])
        print(f"Count: {len(items)}")
        for item in items:
            print(item)
    except Exception as e:
        print(f"Error scanning table: {e}")

if __name__ == "__main__":
    inspect_logs('/aws/lambda/UrbanFlowAnomalyDetector')
    scan_table('UrbanFlowAlerts')
