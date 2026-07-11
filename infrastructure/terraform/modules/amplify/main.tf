resource "aws_amplify_app" "frontend" {
  name       = "${var.project_name}-${var.environment}"
  repository = var.repository_url

  build_spec = <<-EOT
    version: 1
    frontend:
      phases:
        preBuild:
          commands:
            - cd frontend
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: frontend/dist
        files:
          - '**/*'
      cache:
        paths:
          - frontend/node_modules/**/*
  EOT

  environment_variables = {
    VITE_API_URL = var.api_endpoint
  }

  custom_rule {
    source = "/<*>"
    status = "404-200"
    target = "/index.html"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}"
  }
}

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.frontend.id
  branch_name = var.environment == "prod" ? "main" : "dev"

  environment_variables = {
    VITE_API_URL = var.api_endpoint
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-branch"
  }
}
