import boto3
import json
import base64
import time
import random

STREAM_NAME = "urbanflow-input-stream"
kinesis = boto3.client(
    'kinesis', 
    endpoint_url='http://localhost:4566', 
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def send_ghost_driver():
    street_id = "S1"
    
    payload = {
        "street_name": "Main St",
        "street_id": street_id,
        "camera_id": "CAM-S1-01",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "license_plate": "GH 0ST66",
        "speed_kph": -50.5, # GHOST DRIVER!
        "speed_limit": 50,
        "lane_id": 1,
        "vehicle_type": "Car",
        "ocr_confidence": 0.99,
        "is_violation": True,
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    
    data = json.dumps(payload)
    print(f"Sending Ghost Driver Payload: {data}")
    
    kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=data,
        PartitionKey=street_id
    )
    print("Sent!")

if __name__ == "__main__":
    send_ghost_driver()
