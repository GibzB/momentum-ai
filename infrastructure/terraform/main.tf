# --- DynamoDB Tables ---
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

# --- IAM Roles ---
module "iam" {
  source = "./modules/iam"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  projects_table_arn = module.dynamodb.projects_table_arn
  tasks_table_arn    = module.dynamodb.tasks_table_arn
  bedrock_model_id   = var.bedrock_model_id
}

# --- API Gateway ---
module "api_gateway" {
  source = "./modules/api_gateway"

  project_name      = var.project_name
  environment       = var.environment
  lambda_invoke_arn = module.lambda.invoke_arn
}

# --- Lambda Function ---
module "lambda" {
  source = "./modules/lambda"

  project_name              = var.project_name
  environment               = var.environment
  lambda_role_arn           = module.iam.lambda_role_arn
  memory_size               = var.lambda_memory_size
  timeout                   = var.lambda_timeout
  projects_table_name       = module.dynamodb.projects_table_name
  tasks_table_name          = module.dynamodb.tasks_table_name
  bedrock_model_id          = var.bedrock_model_id
  api_gateway_execution_arn = module.api_gateway.execution_arn
}

# --- Monitoring ---
module "monitoring" {
  source = "./modules/monitoring"

  project_name         = var.project_name
  environment          = var.environment
  lambda_function_name = module.lambda.function_name
}

# --- Amplify Frontend ---
module "amplify" {
  source = "./modules/amplify"

  project_name = var.project_name
  environment  = var.environment
  api_endpoint = module.api_gateway.api_endpoint
}

# --- GitHub OIDC (CI/CD) ---
module "github_oidc" {
  source = "./modules/github_oidc"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
  github_repo  = var.github_repo
}
