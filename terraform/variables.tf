variable "region" {
  description = "AWS region for the InfraPilot deployment."
  type        = string
  default     = "ap-south-1"
}

variable "app_instance_type" {
  description = "Small x86 EC2 instance for the portfolio deployment."
  type        = string
  default     = "t3.micro"
}

variable "db_instance_class" {
  description = "Small single-AZ RDS instance for the portfolio deployment."
  type        = string
  default     = "db.t3.micro"
}

variable "db_username" {
  description = "Application database username."
  type        = string
  default     = "infrauser"
}

variable "db_password" {
  description = "Unique RDS password; provide through an ignored terraform.tfvars file."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Use a unique database password with at least 16 characters."
  }
}

variable "image_tag" {
  description = "Immutable ECR tag for the API image to deploy."
  type        = string
  default     = "v1"
}

variable "deploy_app" {
  description = "Set true only after the versioned API image has been pushed to ECR."
  type        = bool
  default     = false
}
