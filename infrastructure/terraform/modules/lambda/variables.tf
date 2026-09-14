variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_role_arn" {
  type = string
}

variable "memory_size" {
  type    = number
  default = 512
}

variable "timeout" {
  type    = number
  default = 30
}

variable "projects_table_name" {
  type = string
}

variable "tasks_table_name" {
  type = string
}

variable "bedrock_model_id" {
  type = string
}

variable "api_gateway_execution_arn" {
  type = string
}

variable "watcher_timeout" {
  type    = number
  default = 300
}

variable "watcher_schedule" {
  description = "EventBridge schedule expression for the background sweep"
  type        = string
  default     = "rate(6 hours)"
}

variable "alert_email" {
  description = "Email to subscribe to M1 alerts (empty = no subscription)"
  type        = string
  default     = ""
}
