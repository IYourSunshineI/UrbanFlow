import json

def lambda_handler(event, context):
    print("Hello from UrbanFlowIngestionProcessor!")
    print("Received event:", json.dumps(event))
    
    # Kinesis events contain records
    if 'Records' in event:
        print(f"Processing {len(event['Records'])} records.")
        for record in event['Records']:
            # Kinesis data is base64 encoded
            print(f"Record ID: {record['eventID']}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Ingestion processed successfully')
    }
