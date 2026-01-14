import json
import os
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

ALERTS_TABLE_NAME = os.getenv('ALERTS_TABLE_NAME')

dynamodb = boto3.resource('dynamodb')
alerts_table = dynamodb.Table(ALERTS_TABLE_NAME) if ALERTS_TABLE_NAME else None

def parse_kinesis_records(records):
    parsed_records = []
    # ... (keeping existing parse logic from previous turn, but simplified re-write for safety)
    import base64
    for record in records:
        try:
            payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            data = json.loads(payload)
            parsed_records.append(data)
        except Exception as e:
            print(f"Error decoding record: {e}")
            continue
    return parsed_records

def lambda_handler(event, context):
    records = event.get("Records", [])
    if not records:
        return

    parsed_records = parse_kinesis_records(records)
    
    for record in parsed_records:
        # Ghost Driver Detection: speed_kph < 0
        speed = record.get('speed_kph', 0)
        
        if speed < 0:
            print(f"👻 GHOST DRIVER DETECTED! Speed: {speed}, Plate: {record.get('license_plate')}")
            
            alert = {
                'alert_id': str(uuid.uuid4()),
                'sensor_id': record.get('street_id'),
                'street_name': record.get('street_name'),
                'timestamp': record.get('timestamp', datetime.now().isoformat()),
                'type': 'GHOST_DRIVER',
                'location': {
                    'lat': Decimal(str(record.get('latitude'))),
                    'lng': Decimal(str(record.get('longitude')))
                },
                'details': {
                    'speed_kph': Decimal(str(speed)),
                    'license_plate': record.get('license_plate')
                },
                'expiration_time': int(datetime.now().timestamp()) + 300 # 5 mins TTL
            }
            
            # Save to DynamoDB
            if alerts_table:
                try:
                    alerts_table.put_item(Item=alert)
                    print(f"Alert saved: {alert['alert_id']}")
                except Exception as e:
                    print(f"Error saving alert: {e}")
