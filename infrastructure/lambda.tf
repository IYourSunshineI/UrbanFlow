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
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"
  filename      = "${path.module}/dummy_lambda/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/dummy_lambda/lambda.zip")
  timeout       = 30
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
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.13"
  filename      = "${path.module}/dummy_lambda/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/dummy_lambda/lambda.zip")
  timeout       = 10
}
