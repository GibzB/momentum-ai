output "api_endpoint" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "execution_arn" {
  value = aws_apigatewayv2_api.http.execution_arn
}

output "api_id" {
  value = aws_apigatewayv2_api.http.id
}
