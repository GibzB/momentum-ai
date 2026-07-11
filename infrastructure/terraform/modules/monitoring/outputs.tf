output "error_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.lambda_errors.arn
}

output "duration_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.lambda_duration.arn
}
