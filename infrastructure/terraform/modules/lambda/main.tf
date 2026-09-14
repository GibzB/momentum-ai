# Lambda function — deployed as zip from CI/CD
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  role          = var.lambda_role_arn
  handler       = "app.main.handler"
  runtime       = "python3.12"
  memory_size   = var.memory_size
  timeout       = var.timeout
  architectures = ["arm64"]

  # Placeholder — real code deployed via CI/CD
  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      DYNAMODB_TABLE_PROJECTS = var.projects_table_name
      DYNAMODB_TABLE_TASKS    = var.tasks_table_name
      BEDROCK_MODEL_ID        = var.bedrock_model_id
      AWS_LWA_INVOKE_MODE     = "response_stream"
    }
  }

  tags = {
    Name = "${var.project_name}-api-${var.environment}"
  }
}

# Placeholder zip for initial deployment
data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    content  = "# Placeholder — deployed via CI/CD"
    filename = "placeholder.py"
  }
}

# CloudWatch Log Group with retention
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = var.environment == "prod" ? 30 : 7
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

# --- Background watcher: scheduled M1 sweep ---
resource "aws_lambda_function" "watcher" {
  function_name = "${var.project_name}-watcher-${var.environment}"
  role          = var.lambda_role_arn
  handler       = "app.agent.watcher.handler"
  runtime       = "python3.12"
  memory_size   = var.memory_size
  timeout       = var.watcher_timeout
  architectures = ["arm64"]

  # One sweep at a time; alert claims are also atomic in DynamoDB as a backstop.
  reserved_concurrent_executions = 1

  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT             = var.environment
      DYNAMODB_TABLE_PROJECTS = var.projects_table_name
      DYNAMODB_TABLE_TASKS    = var.tasks_table_name
      BEDROCK_MODEL_ID        = var.bedrock_model_id
      ALERTS_TOPIC_ARN        = aws_sns_topic.alerts.arn
    }
  }

  tags = {
    Name = "${var.project_name}-watcher-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "watcher" {
  name              = "/aws/lambda/${aws_lambda_function.watcher.function_name}"
  retention_in_days = var.environment == "prod" ? 30 : 7
}

resource "aws_cloudwatch_event_rule" "watcher_schedule" {
  name                = "${var.project_name}-watcher-${var.environment}"
  description         = "Periodic M1 sweep of all projects"
  schedule_expression = var.watcher_schedule
}

resource "aws_cloudwatch_event_target" "watcher" {
  rule = aws_cloudwatch_event_rule.watcher_schedule.name
  arn  = aws_lambda_function.watcher.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.watcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.watcher_schedule.arn
}

# Humans only hear from M1 through this topic
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts-${var.environment}"
}

resource "aws_sns_topic_subscription" "alert_email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
