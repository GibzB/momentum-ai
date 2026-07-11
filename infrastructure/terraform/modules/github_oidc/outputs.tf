output "deploy_role_arn" {
  value       = aws_iam_role.github_deploy.arn
  description = "ARN for GitHub Actions to assume (set as AWS_DEPLOY_ROLE_ARN)"
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}
