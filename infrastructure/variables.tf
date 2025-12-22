variable "lambda_batch_size" {
  description = "Batch size for Kinesis event source mapping"
  type        = number
  default     = 100
}
