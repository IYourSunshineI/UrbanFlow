import re
from datetime import datetime
import boto3
import os
import json
import base64

AGGREGATION_FUNCTION_NAME = os.getenv('AGGREGATION_FUNCTION_NAME')

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
}

VEHICLE_TYPES = ["Car", "Car", "Car", "Truck", "Motorcycle", "Bus"]

MAX_VALID_SPEED = 299
MIN_OCR_CONFIDENCE = 0.50


def validate_schema(payload):
    for field, field_type in FIELDS.items():
        if field not in payload:
            return False, f"Missing field: {field}"
        if not isinstance(payload[field], field_type):
            return False, f"Incorrect type for field: {field}. Expected {field_type.__name__}, got {type(payload[field]).__name__}"
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

    return True, None


def forward_to_aggregation(payload):
    if not AGGREGATION_FUNCTION_NAME:
        print("AGGREGATION_FUNCTION_NAME is not set. Skipping invoke...")
        return

    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=AGGREGATION_FUNCTION_NAME,
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8'))


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
