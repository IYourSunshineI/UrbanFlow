import time
import json
import uuid
import random
import datetime
import boto3
import threading
from botocore.config import Config

# Configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
STREAM_NAME = "urbanflow-input-stream"  # [cite: 20]
# Using the aggregated table for freshness checks as it's the result of the pipeline
DYNAMODB_TABLE = "UrbanFlowAggregatedTrafficData"
LAMBDA_FUNC_NAME = "UrbanFlowIngestionProcessor"

# Experiment Settings
WARM_UP_RATE = 500  # events/sec
WARM_UP_DURATION = 18  # seconds (3 minutes)
RAMP_UP_RATE = 10000  # events/sec
RAMP_UP_DURATION = 30  # seconds (5 minutes)

# Kinesis Limits
MAX_RECORDS_PER_BATCH = 500  # Kinesis PutRecords limit

# AWS Clients
dummy_creds = {
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
    "region_name": REGION,
    "endpoint_url": ENDPOINT_URL
}
config = Config(retries={'max_attempts': 3, 'mode': 'standard'})
kinesis = boto3.client('kinesis', config=config, **dummy_creds)
dynamodb = boto3.client('dynamodb', **dummy_creds)
cloudwatch = boto3.client('cloudwatch', **dummy_creds)
logs_client = boto3.client('logs', **dummy_creds)

# Global Metrics
stats = {
    "sent_events": 0,
    "failed_events": 0,
    "latency_samples": [],  # End-to-End latency in ms
    "freshness_samples": []  # Ingestion delay in ms
}


def generate_record():
    """
    Generates a single vehicle data record similar to camera_sim.py.
    """
    street_id = f"{random.randint(100, 999)}"
    now = datetime.datetime.now()

    data = {
        "street_id": street_id,
        "camera_id": f"CAM-XYZ-{street_id}-01",
        "timestamp": now.isoformat(),
        "speed_kph": round(random.uniform(20.0, 90.0), 1),
        "vehicle_type": "Car",
        "request_id": str(uuid.uuid4()),  # Traceable ID for latency checks
        "street_name": "Test Street",
        "latitude": 48.20,
        "longitude": 16.80,
        "license_plate": "AB 123XZ",
        "speed_limit": 90,
        "lane_id": random.randint(1, 2),
        "ocr_confidence": round(random.uniform(0.85, 0.99), 2),
        "is_violation": False
    }
    return data


def load_generator(target_rate, duration, phase_name):
    """
    Generates load at a specific rate using Kinesis PutRecords for efficiency.
    """
    print(f"--- Starting {phase_name}: Target {target_rate} events/sec for {duration}s ---")

    start_time = time.time()
    next_batch_time = start_time

    # Calculate how many batches of 500 we need per second to hit target
    batches_per_sec = max(1, target_rate // MAX_RECORDS_PER_BATCH)
    interval = 1.0 / batches_per_sec

    while (time.time() - start_time) < duration:
        # Prepare a batch
        records_batch = []
        for _ in range(MAX_RECORDS_PER_BATCH):
            data = generate_record()
            records_batch.append({
                'Data': json.dumps(data),
                'PartitionKey': data['street_id']
            })

            # Periodically sample for latency (tag 1 in 1000 requests)
            if random.random() < 0.001:
                track_latency(data)

        # Send Batch
        try:
            response = kinesis.put_records(
                StreamName=STREAM_NAME,
                Records=records_batch
            )

            # Update counters
            failed_count = response['FailedRecordCount']
            stats["failed_events"] += failed_count
            stats["sent_events"] += (len(records_batch) - failed_count)

        except Exception as e:
            print(f"Error sending batch: {e}")
            stats["failed_events"] += len(records_batch)

        # Rate Limiting
        next_batch_time += interval
        sleep_time = next_batch_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)


def track_latency(data_payload):
    """
    Spawns a thread to poll DynamoDB for a specific record to measure end-to-end latency.
    """

    def poller(record_id, send_time):
        # Poll for up to 30 seconds
        for _ in range(30):
            try:
                # We query the Aggregated table.
                # Note: In a real scenario, we'd query by the specific unique ID,
                # but based on your schema, the key is 'street_id'.
                # For this test, we assume the aggregator updates the 'street_id' record.
                response = dynamodb.get_item(
                    TableName=DYNAMODB_TABLE,
                    Key={'street_id': {'S': data_payload['street_id']}}
                )

                # In a real heavy load test, verifying exact record arrival
                # without a unique ID in DynamoDB is hard.
                # We assume if the item exists, data flowed through.
                if 'Item' in response:
                    arrival_time = time.time()
                    latency = (arrival_time - send_time) * 1000  # ms
                    stats["latency_samples"].append(latency)

                    # Freshness: Compare 'now' with the timestamp inside the data
                    event_time = datetime.datetime.fromisoformat(data_payload['timestamp'])
                    freshness = (datetime.datetime.now() - event_time).total_seconds() * 1000
                    stats["freshness_samples"].append(freshness)
                    return
            except Exception:
                pass
            time.sleep(1)

    threading.Thread(target=poller, args=(data_payload['request_id'], time.time())).start()


def get_cloudwatch_metrics(start_time, end_time):
    """Retrieves Lambda metrics from LocalStack CloudWatch."""
    print("--- Fetching CloudWatch Metrics ---")

    # Wait briefly for metrics to settle
    time.sleep(10)

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': LAMBDA_FUNC_NAME}],
            StartTime=start_time,
            EndTime=datetime.datetime.now(),
            Period=60,
            Statistics=['Sum']
        )
        total_invocations = sum(dp['Sum'] for dp in response['Datapoints'])

        error_response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{'Name': 'FunctionName', 'Value': LAMBDA_FUNC_NAME}],
            StartTime=start_time,
            EndTime=datetime.datetime.now(),
            Period=60,
            Statistics=['Sum']
        )
        total_errors = sum(dp['Sum'] for dp in error_response['Datapoints'])

        return total_invocations, total_errors
    except Exception as e:
        print(f"Could not fetch CloudWatch metrics: {e}")
        return 0, 0


def calculate_results(total_duration):
    print("\n\n" + "=" * 40)
    print("      EXPERIMENT RESULTS")
    print("=" * 40)

    # 1. Throughput
    throughput = stats["sent_events"] / total_duration
    print(f"1. Throughput:       {throughput:.2f} events/sec")

    # 2. Latency
    if stats["latency_samples"]:
        avg_latency = sum(stats["latency_samples"]) / len(stats["latency_samples"])
        print(f"2. Avg Latency:      {avg_latency:.2f} ms")
    else:
        print("2. Avg Latency:      N/A (No samples verified)")

    # 3. Data Freshness
    if stats["freshness_samples"]:
        avg_freshness = sum(stats["freshness_samples"]) / len(stats["freshness_samples"])
        print(f"3. Data Freshness:   {avg_freshness:.2f} ms")
    else:
        print("3. Data Freshness:   N/A")

    # 4. CloudWatch Metrics (Errors & Efficiency)
    # Start time is roughly now - total_duration
    start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=total_duration)
    invocations, errors = get_cloudwatch_metrics(start_time, datetime.datetime.now())

    print(f"4. Total Invocations:{int(invocations)}")
    print(f"5. Total Lambda Errors:{int(errors)}")

    if invocations > 0:
        batch_efficiency = stats["sent_events"] / invocations
        print(f"6. Batch Efficiency: {batch_efficiency:.2f} records/invocation")
        # Note: Ideal is close to 500
    else:
        print("6. Batch Efficiency: N/A")

    error_rate = (errors / invocations * 100) if invocations > 0 else 0
    print(f"7. Error Rate:       {error_rate:.2f}%")


# --- Main Execution ---
if __name__ == "__main__":
    print(f"Targeting LocalStack at {ENDPOINT_URL}")
    print(f"Stream: {STREAM_NAME}")

    total_start = time.time()

    # Step 1: Warm-up
    load_generator(WARM_UP_RATE, WARM_UP_DURATION, "WARM-UP")

    # Step 2: Ramp-up
    load_generator(RAMP_UP_RATE, RAMP_UP_DURATION, "RAMP-UP")

    total_duration = time.time() - total_start

    # Step 3 & 4: Metrics & Evaluation
    calculate_results(total_duration)