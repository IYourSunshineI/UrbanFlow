resource "aws_sqs_queue" "urbanflow_aggregation_queue" {
  name                       = "UrbanFlowAggregationQueue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600
}