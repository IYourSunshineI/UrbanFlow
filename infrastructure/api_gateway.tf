resource "aws_apigatewayv2_api" "urbanflow_api" {
  name          = "UrbanFlowAPI"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.urbanflow_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "reader_lambda_integration" {
  api_id           = aws_apigatewayv2_api.urbanflow_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.data_reader.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.urbanflow_api.id
  route_key = "GET /traffic"
  target    = "integrations/${aws_apigatewayv2_integration.reader_lambda_integration.id}"
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_reader.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.urbanflow_api.execution_arn}/*/*"
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.urbanflow_api.api_endpoint
}
