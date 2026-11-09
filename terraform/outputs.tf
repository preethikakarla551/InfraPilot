output "ecr_repository_url" {
  description = "Private ECR repository for the InfraPilot API image."
  value       = aws_ecr_repository.api.repository_url
}

output "database_endpoint" {
  description = "Private RDS endpoint; reachable only from the application security group."
  value       = aws_db_instance.infrapilot.address
}

output "application_public_ip" {
  description = "Public IP of the application host, after the app deployment stage."
  value       = try(aws_instance.app[0].public_ip, null)
}

output "public_health_url" {
  description = "Public read-only health endpoint; the other API routes are blocked at Nginx."
  value       = try("http://${aws_instance.app[0].public_ip}/health", null)
}

output "ssm_instance_id" {
  description = "Use AWS Systems Manager Session Manager for administration; no SSH port is open."
  value       = try(aws_instance.app[0].id, null)
}
