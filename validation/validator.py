import re
from datetime import datetime
import boto3
import os
import json

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

    if not re.match(CAMERA_ID_PATTERN, payload["camera_id"]):
        return False, "camera_id format is invalid"

    try:
        datetime.fromisoformat(str(payload["timestamp"]))
    except ValueError:
        return False, "timestamp format is invalid"

    if not re.match(LICENSE_PLATE_PATTERN, payload["license_plate"]):
        return False, "license_plate format is invalid"

    if payload["speed_kph"] < 0 or payload["speed_limit"] > MAX_VALID_SPEED:
        return False, "Invalid speed_kph value"

    if payload["lane_id"] < 1:
        return False, "lane_id must be >= 1"

    if payload["vehicle_type"] not in VEHICLE_TYPES:
        return False, "Unknown vehicle_type"

    if payload["ocr_confidence"] <= MIN_OCR_CONFIDENCE:
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


def get_caller_ip(event):
    try:
        # REST API
        return event["requestContext"]["identity"]["sourceIp"]
    except KeyError:
        try:
            # HTTP API
            return event["requestContext"]["http"]["sourceIp"]
        except KeyError:
            return "unknown"


def lambda_handler(event, context):
    print(f"Validating data from: {get_caller_ip(event)}")
    is_valid, error_message = validate_schema(event)
    if not is_valid:
        print(f"Validation failed: {error_message}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error_message})
        }

    is_valid, error_message = validate_data(event)
    if not is_valid:
        print(f"Validation failed: {error_message}")
        return {
            'statusCode': 422,
            'body': json.dumps({'error': error_message})
        }

    forward_to_aggregation(event)

    return {
        'statusCode': 202,
        'body': json.dumps({'status': 'accepted'})
    }
