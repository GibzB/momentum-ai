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
