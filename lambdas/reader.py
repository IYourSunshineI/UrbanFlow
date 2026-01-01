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


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    street_id = params.get("street_id")

    if not street_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "street_id parameter is required"})
        }

    if not street_id_exists(street_id):
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "street_id not found"})
        }

    try:
        data = get_latest_data_for_street(street_id)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(data, default=decimal_to_float)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def get_latest_data_for_street(street_id):
    res = table.query(
        KeyConditionExpression="street_id = :sid",
        ExpressionAttributeValues={":sid": street_id},
        ScanIndexForward=False,
        Limit=1
    )
    return res.get("Items", [])
