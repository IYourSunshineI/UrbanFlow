resource "aws_dynamodb_table" "traffic_data" {
  name           = "UrbanFlowTrafficData"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "segment_id"
  range_key      = "timestamp"

  attribute {
    name = "segment_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  ttl {
    attribute_name = "expiration_time"
    enabled        = true
  }
}

# Additional table for aggregated data
resource "aws_dynamodb_table" "aggregated_traffic_data" {
  name           = "UrbanFlowAggregatedTrafficData"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "street_id"

  attribute {
    name = "street_id"
    type = "S"
  }
}