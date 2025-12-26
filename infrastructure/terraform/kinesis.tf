resource "aws_kinesis_stream" "urbanflow_input_stream" {
  name             = "urbanflow-input-stream"
  shard_count      = 1
  retention_period = 24

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
  ]
}
