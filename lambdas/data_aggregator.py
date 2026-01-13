import json
import base64
from time import time
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'StreetSpeedAggregates')
table = dynamodb.Table(TABLE_NAME)

lambda_client = boto3.client('lambda')
CALCULATION_ARN = os.environ.get('CONGESTION_CALCULATION_ARN')

def lambda_handler(event, context):
    """
    Triggered by Validation Lambda.
    """
    data_points = event

    if not isinstance(data_points, list):
        print(f"Unexpected data format. Expected list, got {type(data_points)}")
        return {'statusCode': 400, 'message': 'Invalid data format'}
    
    if not data_points:
        print("No valid data points found.")
        return {'statusCode': 200, 'message': 'No data points to process'}
    
    street_stats = aggregate_metrics(data_points)
    timestamp = datetime.now().isoformat()
    persist_aggregated_data(street_stats, timestamp)

    return {'statusCode': 200, 'message': 'Data aggregated and persisted'}

def aggregate_metrics(data_points):
    """
    Helper function to aggregate metrics from data points.
    """
    stats = {}

    for data in data_points:
        s_id = data.get('street_id')
        speed = data.get('speed_kph', 0)
        limit = data.get('speed_limit', 0)
        s_name = data.get('street_name', 'Unknown')
        license_plate = data.get('license_plate', 'Unknown')
        lat = data.get('latitude', 0)
        lng = data.get('longitude', 0)

        if s_id not in stats:
            stats[s_id] = {
                'street_name': s_name,
                'total_speed': 0,
                'vehicle_count': 0,
                'speed_limit': limit,
                'license_plates': set(),
                'latitude': lat,
                'longitude': lng
            }
        stats[s_id]['total_speed'] += speed
        if license_plate not in stats[s_id]['license_plates']:
            stats[s_id]['license_plates'].add(license_plate)
            stats[s_id]['vehicle_count'] += 1

    return stats

def get_congestion_index(speed_limit, avg_speed):
    """
    Invoke congestion index calculation function
    """
    if not CALCULATION_ARN:
        print("Congestion calculation ARN not set.")
        return -1

    try:
        invoke_payload = {
            'speed_limit': speed_limit,
            'avg_speed': avg_speed
        }

        response = lambda_client.invoke(
            FunctionName=CALCULATION_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(invoke_payload)
        )

        response_payload = json.loads(response['Payload'].read())
        return response_payload.get('congestion_index', -1)

    except Exception as e:
        print(f"Error invoking congestion calculation function: {e}")
        return -1

def persist_aggregated_data(street_stats, timestamp):
    """
    Persist aggregated data to DynamoDB.
    """

    with table.batch_writer() as batch:
        for s_id, stats in street_stats.items():
            avg_speed = stats['total_speed'] / stats['vehicle_count'] if stats['vehicle_count'] > 0 else 0

            congestion_index = get_congestion_index(stats['speed_limit'], avg_speed)

            item = {
                'street_id': s_id,
                'street_name': stats['street_name'],
                'average_speed_kph': Decimal(str(round(avg_speed, 2))),
                'speed_limit_kph': stats['speed_limit'],
                'vehicle_count': stats['vehicle_count'],
                'congestion_index': Decimal(str(round(congestion_index, 4))),
                'timestamp_utc': timestamp,
                'latitude': Decimal(str(stats['latitude'])),
                'longitude': Decimal(str(stats['longitude']))
            }
            batch.put_item(Item=item)

    print(f"Saved aggregated data for {len(street_stats)} streets to DynamoDB.")