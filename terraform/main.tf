variable "region" {
  description = "AWS region for the example network."
  type        = string
  default     = "us-east-1"
}

provider "aws" {
  region = var.region
}

resource "aws_vpc" "infrapilot" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "infrapilot-demo" }
}

resource "aws_subnet" "private_a" {
  vpc_id                  = aws_vpc.infrapilot.id
  cidr_block              = "10.42.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = false
  tags                    = { Name = "infrapilot-private-a" }
}

output "vpc_id" {
  value = aws_vpc.infrapilot.id
}
