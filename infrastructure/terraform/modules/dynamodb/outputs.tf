output "projects_table_name" {
  value = aws_dynamodb_table.projects.name
}

output "projects_table_arn" {
  value = aws_dynamodb_table.projects.arn
}

output "tasks_table_name" {
  value = aws_dynamodb_table.tasks.name
}

output "tasks_table_arn" {
  value = aws_dynamodb_table.tasks.arn
}
