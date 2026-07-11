output "app_id" {
  value = aws_amplify_app.frontend.id
}

output "default_domain" {
  value = aws_amplify_app.frontend.default_domain
}

output "branch_url" {
  value = "https://${aws_amplify_branch.main.branch_name}.${aws_amplify_app.frontend.default_domain}"
}
