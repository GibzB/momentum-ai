variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "github_repo" {
  description = "GitHub repo in format owner/repo"
  type        = string
}
