output "website_url" {
  value = "http://${aws_s3_bucket.angular_host.bucket}.s3-website.localhost.localstack.cloud:4566"
}

output "api_url" {
  value = aws_api_gateway_stage.dev.invoke_url
}

output "api_id" {
  value = aws_api_gateway_rest_api.urbanflow_api.id
}

output "lambda_path" {
  value = "$${HOST_LAMBDA_DIR}/lambdas/"
}