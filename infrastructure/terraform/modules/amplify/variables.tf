variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "repository_url" {
  type        = string
  description = "GitHub repository URL"
}

variable "api_endpoint" {
  type        = string
  description = "Backend API Gateway endpoint"
}
