import re
from datetime import datetime
import boto3
import os
import json
import base64

AGGREGATION_QUEUE_URL = os.getenv('AGGREGATION_QUEUE_URL')

CAMERA_ID_PATTERN = re.compile(r'CAM-[A-Z]{3}-\d{3}-\d{2}')
LICENSE_PLATE_PATTERN = re.compile(r'[A-Z]{2} \d{3}[A-Z]{2}')

FIELDS = {
    "street_name": str,
    "street_id": str,
    "camera_id": str,
    "timestamp": str,
    "license_plate": str,
    "speed_kph": (int, float),
    "speed_limit": (int, float),
    "lane_id": int,
    "vehicle_type": str,
    "ocr_confidence": (int, float),
    "is_violation": bool,
    "latitude": (int, float),
    "longitude": (int, float),
}

VEHICLE_TYPES = ["Car", "Car", "Car", "Truck", "Motorcycle", "Bus"]

MAX_VALID_SPEED = 299
MIN_OCR_CONFIDENCE = 0.50


def validate_schema(payload):
    for field, field_type in FIELDS.items():
        if field not in payload:
            return False, f"Missing field: {field}"
        if not isinstance(payload[field], field_type):
            return False, f"Incorrect type for field: {field}. Expected {field_type}, got {type(payload[field]).__name__}"
    return True, None


def validate_data(payload):
    if payload["street_name"] == "":
        return False, "street_name cannot be empty"

    if payload["street_id"] == "":
        return False, "street_id cannot be empty"

    if not CAMERA_ID_PATTERN.match(payload["camera_id"]):
        return False, "camera_id format is invalid"

    try:
        datetime.fromisoformat(str(payload["timestamp"]))
    except ValueError:
        return False, "timestamp format is invalid"

    if not LICENSE_PLATE_PATTERN.match(payload["license_plate"]):
        return False, "license_plate format is invalid"

    if payload["speed_kph"] < 0 or payload["speed_kph"] > MAX_VALID_SPEED:
        return False, "Invalid speed_kph value"

    if payload["lane_id"] < 1:
        return False, "lane_id must be >= 1"

    if payload["vehicle_type"] not in VEHICLE_TYPES:
        return False, "Unknown vehicle_type"

    if payload["ocr_confidence"] < MIN_OCR_CONFIDENCE:
        return False, "ocr_confidence is too low"

    if payload["ocr_confidence"] > 1.0:
        return False, "ocr_confidence cannot be greater than 1.0"

    if payload["latitude"] < -90 or payload["latitude"] > 90:
        return False, "latitude must be between -90 and 90"

    if payload["longitude"] < -180 or payload["longitude"] > 180:
        return False, "longitude must be between -180 and 180"

    return True, None


def forward_to_aggregation(valid_records):
    if not AGGREGATION_QUEUE_URL:
        print("AGGREGATION_QUEUE_URL is not set. Skipping send...")
        return

    sqs_client = boto3.client('sqs')
    
    # Batch send message to SQS (max 10 per batch call)
    # We iterate and send in chunks
    chunk_size = 10
    
    for i in range(0, len(valid_records), chunk_size):
        chunk = valid_records[i:i + chunk_size]
        entries = []
        for idx, record in enumerate(chunk):
            entries.append({
                'Id': str(idx),
                'MessageBody': json.dumps(record)
            })
            
        try:
            sqs_client.send_message_batch(
                QueueUrl=AGGREGATION_QUEUE_URL,
                Entries=entries
            )
            print(f"Sent batch of {len(entries)} records to SQS")
        except Exception as e:
            print(f"Failed to send batch to SQS: {e}")


def parse_kinesis_records(records):
    parsed_records = []
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
        print("No records found in event")
        return

    parsed_records = parse_kinesis_records(records)
    print(f"Validating {len(parsed_records)} records...")
    valids = []
    for record in parsed_records:
        is_valid, error_message = validate_schema(record)
        if not is_valid:
            print(f"Schema validation failed: {record} - {error_message}")
            continue

        is_valid, error_message = validate_data(record)
        if not is_valid:
            print(f"Data validation failed: {record} - {error_message}")
            continue

        valids.append(record)

    if not valids:
        print("No valid records to forward")
        return

    print(f"Forwarding {len(valids)} valid records to aggregation")
    forward_to_aggregation(valids)
