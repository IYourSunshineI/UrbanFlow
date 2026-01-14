import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.getenv("AGGREGATED_DATA_TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)


def decimal_to_float(val):
    if isinstance(val, Decimal):
        return float(val)
    else:
        raise TypeError


def street_id_exists(street_id):
    res = table.get_item(
        Key={"street_id": street_id}
    )
    return "Item" in res


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, OPTIONS"
}


def lambda_handler(event, context):
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": ""
        }

    params = event.get("queryStringParameters") or {}
    street_id = params.get("street_id")

    try:
        # If no street_id provided, return all streets' latest data
        if not street_id:
            data = get_all_latest_data()
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps(data, default=decimal_to_float)
            }

        # Single street lookup
        if not street_id_exists(street_id):
            return {
                "statusCode": 404,
                "headers": CORS_HEADERS,
                "body": json.dumps({"error": "street_id not found"})
            }

        data = get_latest_data_for_street(street_id)
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(data, default=decimal_to_float)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(e)})
        }


def get_latest_data_for_street(street_id):
    res = table.query(
        KeyConditionExpression="street_id = :sid",
        ExpressionAttributeValues={":sid": street_id},
        ScanIndexForward=False,
        Limit=1
    )
    items = res.get("Items", [])
    return items[0] if items else None


def get_all_latest_data():
    """
    Scan entire table and return the latest entry for each street.
    Note: For production with large datasets, consider using a GSI or
    maintaining a separate 'latest' table for efficiency.
    """
    all_items = []
    last_key = None

    # Paginated scan
    while True:
        if last_key:
            response = table.scan(ExclusiveStartKey=last_key)
        else:
            response = table.scan()

        all_items.extend(response.get("Items", []))
        last_key = response.get("LastEvaluatedKey")

        if not last_key:
            break

    # Group by street_id and get latest (by timestamp_utc) for each
    latest_by_street = {}
    for item in all_items:
        street_id = item.get("street_id")
        timestamp = item.get("timestamp_utc", "")

        if street_id not in latest_by_street:
            latest_by_street[street_id] = item
        else:
            existing_ts = latest_by_street[street_id].get("timestamp_utc", "")
            if timestamp > existing_ts:
                latest_by_street[street_id] = item

    return list(latest_by_street.values())
