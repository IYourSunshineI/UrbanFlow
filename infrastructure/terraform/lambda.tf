resource "aws_iam_role" "lambda_exec" {
  name = "urbanflow_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_kinesis_dynamodb_policy" {
  name        = "urbanflow_lambda_policy"
  description = "IAM policy for Kinesis and DynamoDB access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:GetRecords",
          "kinesis:GetShardIterator",
          "kinesis:DescribeStream",
          "kinesis:ListStreams",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_custom_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_kinesis_dynamodb_policy.arn
}

resource "aws_lambda_function" "ingestion_processor" {
  function_name = "UrbanFlowIngestionProcessor"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "validator.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30

  # Localstack Hot-Reload
  s3_bucket = "hot-reload"
  s3_key    = "$${HOST_LAMBDA_DIR}"

  environment {
    variables = {
      AGGREGATION_FUNCTION_NAME = aws_lambda_function.data_aggregator.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "kinesis_trigger" {
  event_source_arn  = aws_kinesis_stream.urbanflow_input_stream.arn
  function_name     = aws_lambda_function.ingestion_processor.arn
  starting_position = "LATEST"
  batch_size        = var.lambda_batch_size
}

resource "aws_lambda_function" "data_reader" {
  function_name = "UrbanFlowDataReader"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "data_reader.lambda_handler"
  runtime       = "python3.13"
  timeout       = 10

  # Localstack Hot-Reload
  s3_bucket = "hot-reload"
  s3_key    = "$${HOST_LAMBDA_DIR}"

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.aggregated_traffic_data.name
    }
  }
}

resource "aws_lambda_function" "data_aggregator" {
  function_name = "UrbanFlowDataAggregator"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "data_aggregator.lambda_handler"
  runtime       = "python3.13"
  timeout       = 20

  # Localstack Hot-Reload
  s3_bucket = "hot-reload"
  s3_key    = "$${HOST_LAMBDA_DIR}"

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.aggregated_traffic_data.name
      CONGESTION_CALCULATION_ARN = aws_lambda_function.congestion_calculation.arn
      RETENTION_DAYS = "30" #Data retention period
    }
  }
}

resource "aws_lambda_function" "congestion_calculation" {
  function_name = "UrbanFlowCongestionCalculation"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "congestion_calculation.lambda_handler"
  runtime       = "python3.13"
  timeout       = 10

  # Localstack Hot-Reload
  s3_bucket = "hot-reload"
  s3_key    = "$${HOST_LAMBDA_DIR}"
}
