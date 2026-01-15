variable "lambda_batch_size" {
  description = "Batch size for Kinesis event source mapping"
  type        = number
  default     = 100
}

variable "aggregation_batch_size" {
  description = "Batch size for SQS event source mapping"
  type        = number
  default     = 100
}

variable "aggregation_batch_window" {
  description = "Batch window for SQS event source mapping"
  type        = number
  default     = 60
}
