resource "aws_api_gateway_rest_api" "urbanflow_api" {
  name        = "UrbanFlowAPI"
  description = "UrbanFlow REST API (V1)"
}

resource "aws_api_gateway_resource" "traffic" {
  rest_api_id = aws_api_gateway_rest_api.urbanflow_api.id
  parent_id   = aws_api_gateway_rest_api.urbanflow_api.root_resource_id
  path_part   = "traffic"
}

resource "aws_api_gateway_method" "get_traffic" {
  rest_api_id   = aws_api_gateway_rest_api.urbanflow_api.id
  resource_id   = aws_api_gateway_resource.traffic.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.urbanflow_api.id
  resource_id = aws_api_gateway_resource.traffic.id
  http_method = aws_api_gateway_method.get_traffic.http_method

  integration_http_method = "POST" # Lambda invoke must be POST
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.data_reader.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.urbanflow_api.id
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.deployment.id
  rest_api_id   = aws_api_gateway_rest_api.urbanflow_api.id
  stage_name    = "dev"
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_reader.function_name
  principal     = "apigateway.amazonaws.com"

  # More permissive source_arn to allow any stage/method
  source_arn    = "${aws_api_gateway_rest_api.urbanflow_api.execution_arn}/*/*"
}
