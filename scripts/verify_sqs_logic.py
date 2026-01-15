
import unittest
from unittest.mock import MagicMock, patch
import os
import json
import sys

# Add lambdas directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../lambdas')))

# Mock boto3 before importing lambdas
sys.modules['boto3'] = MagicMock()

import validator
import data_aggregator

class TestSQSFlow(unittest.TestCase):
    def setUp(self):
        # Setup mocks
        self.mock_sqs = MagicMock()
        self.mock_boto3_client = MagicMock(return_value=self.mock_sqs)
        validator.boto3.client = self.mock_boto3_client
        
        # Set env var
        validator.AGGREGATION_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/UrbanFlowAggregationQueue"

    def test_validator_producer_batch(self):
        print("\nTesting Validator Producer Logic...")
        # Create 15 dummy records (should result in 2 batches: 10 + 5)
        records = [{"id": i, "content": "data"} for i in range(15)]
        
        validator.forward_to_aggregation(records)
        
        # Verify 2 calls to send_message_batch
        self.assertEqual(self.mock_sqs.send_message_batch.call_count, 2)
        print("Validator correctly batched calls to SQS.")

    def test_aggregator_consumer_logic(self):
        print("\nTesting Aggregator Consumer Logic...")
        
        # Create a dummy SQS event with 2 records
        record_body_1 = json.dumps({"street_id": "S1", "speed_kph": 50, "vehicle_type": "Car", "license_plate": "A"})
        record_body_2 = json.dumps({"street_id": "S1", "speed_kph": 60, "vehicle_type": "Car", "license_plate": "B"})
        
        event = {
            "Records": [
                {"body": record_body_1},
                {"body": record_body_2}
            ]
        }
        
        # Mock aggregator's internal calls (Dynamo, Congestion calc)
        data_aggregator.persist_aggregated_data = MagicMock()
        data_aggregator.get_congestion_index = MagicMock(return_value=1.0) # Mock if needed inside aggregate_metrics
        
        # Invoke handler
        response = data_aggregator.lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], 200)
        
        # Calculate expected average: (50+60)/2 = 55
        # Check if persist_aggregated_data was called with correct data
        args, _ = data_aggregator.persist_aggregated_data.call_args
        street_stats = args[0]
        self.assertIn("S1", street_stats)
        self.assertEqual(street_stats["S1"]["total_speed"], 110)
        self.assertEqual(street_stats["S1"]["vehicle_count"], 2)
        print("Aggregator correctly processed SQS records.")

if __name__ == '__main__':
    unittest.main()
