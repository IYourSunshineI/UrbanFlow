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
