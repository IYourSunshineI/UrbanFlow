import time
import json
import uuid
import random
import datetime
import boto3
import threading
import csv
from botocore.config import Config

# Configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
STREAM_NAME = "urbanflow-input-stream"
# Using the aggregated table for freshness checks as it's the result of the pipeline
DYNAMODB_TABLE = "UrbanFlowAggregatedTrafficData"
LAMBDA_FUNC_NAME = "UrbanFlowIngestionProcessor"
CSV_FILENAME = "latency_freshness_results.csv"

# Experiment Settings
WARM_UP_RATE = 500  # events/sec
WARM_UP_DURATION = 18  # seconds (3 minutes)
RAMP_UP_RATE = 10000  # events/sec
RAMP_UP_DURATION = 30  # seconds (5 minutes)

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
    "freshness_samples": [],  # Ingestion delay in ms
    "sample_timestamps": [] # Timestamps for when the samples were recorded
}
stats_lock = threading.Lock()


def generate_record():
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
    print(f"--- Starting {phase_name}: Target {target_rate} events/sec for {duration}s ---")

    start_time = time.time()
    next_batch_time = start_time

    BATCH_SIZE = 500

    # Calculate how many BATCHES we need per second
    batches_per_sec = max(1, target_rate // BATCH_SIZE)
    interval = 1.0 / batches_per_sec

    while (time.time() - start_time) < duration:
        # Prepare a Batch
        records_batch = []

        for _ in range(BATCH_SIZE):
            data = generate_record()

            # Randomly track latency for one item in the batch
            if random.random() < 0.001:
                track_latency(data)

            records_batch.append({
                'Data': json.dumps(data),
                'PartitionKey': data['street_id']
            })

        # Send the Batch (One HTTP request instead of 500)
        try:
            kinesis.put_records(
                StreamName=STREAM_NAME,
                Records=records_batch
            )
            with stats_lock:
                stats["sent_events"] += len(records_batch)
        except Exception as e:
            print(f"Batch failed: {e}")
            with stats_lock:
                stats["failed_events"] += len(records_batch)

        # Rate Limiting
        next_batch_time += interval
        sleep_time = next_batch_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

def track_latency(data_payload):
    def poller(record_id, send_time):
        # Poll for up to 30 seconds
        for _ in range(30):
            try:
                response = dynamodb.get_item(
                    TableName=DYNAMODB_TABLE,
                    Key={'street_id': {'S': data_payload['street_id']}}
                )

                if 'Item' in response:
                    arrival_time = time.time()
                    latency = (arrival_time - send_time) * 1000  # ms
                    
                    # Freshness: Compare 'now' with the timestamp inside the data
                    event_time = datetime.datetime.fromisoformat(data_payload['timestamp'])
                    freshness = (datetime.datetime.now() - event_time).total_seconds() * 1000
                    
                    with stats_lock:
                        stats["latency_samples"].append(latency)
                        stats["freshness_samples"].append(freshness)
                        stats["sample_timestamps"].append(datetime.datetime.now().isoformat())
                    return
            except Exception:
                pass
            time.sleep(1)

    threading.Thread(target=poller, args=(data_payload['request_id'], time.time())).start()


def get_cloudwatch_metrics(start_time, end_time):
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
    else:
        print("6. Batch Efficiency: N/A")

    error_rate = (errors / invocations * 100) if invocations > 0 else 0
    print(f"7. Error Rate:       {error_rate:.2f}%")
    
    # Save detailed samples to CSV
    save_samples_to_csv()


def save_samples_to_csv():
    try:
        with open(CSV_FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "latency_ms", "freshness_ms"])

            for ts, lat, fresh in zip(stats["sample_timestamps"], stats["latency_samples"], stats["freshness_samples"]):
                writer.writerow([ts, f"{lat:.2f}", f"{fresh:.2f}"])
                
        print(f"\nDetailed samples saved to {CSV_FILENAME}")
    except Exception as e:
        print(f"Error saving CSV: {e}")


if __name__ == "__main__":
    print(f"Targeting LocalStack at {ENDPOINT_URL}")
    print(f"Stream: {STREAM_NAME}")

    total_start = time.time()

    # Step 1: Warm-up
    load_generator(WARM_UP_RATE, WARM_UP_DURATION, "WARM-UP")

    # Step 2: Ramp-up
    load_generator(RAMP_UP_RATE, RAMP_UP_DURATION, "RAMP-UP")

    total_duration = time.time() - total_start

    # Step 3: Metrics & Evaluation
    calculate_results(total_duration)
