output "function_name" {
  value = aws_lambda_function.api.function_name
}

output "function_arn" {
  value = aws_lambda_function.api.arn
}

output "invoke_arn" {
  value = aws_lambda_function.api.invoke_arn
}

output "watcher_function_name" {
  value = aws_lambda_function.watcher.function_name
}

output "alerts_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
