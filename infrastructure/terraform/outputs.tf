output "api_endpoint" {
  description = "HTTP API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda.function_name
}

output "projects_table_name" {
  description = "DynamoDB projects table name"
  value       = module.dynamodb.projects_table_name
}

output "tasks_table_name" {
  description = "DynamoDB tasks table name"
  value       = module.dynamodb.tasks_table_name
}
