provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "InfraPilot"
      Environment = "portfolio"
      ManagedBy   = "Terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

resource "aws_vpc" "infrapilot" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "infrapilot-vpc" }
}

resource "aws_internet_gateway" "infrapilot" {
  vpc_id = aws_vpc.infrapilot.id
  tags   = { Name = "infrapilot-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.infrapilot.id
  cidr_block              = "10.42.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags                    = { Name = "infrapilot-public" }
}

resource "aws_subnet" "database_a" {
  vpc_id            = aws_vpc.infrapilot.id
  cidr_block        = "10.42.10.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]
  tags              = { Name = "infrapilot-database-a" }
}

resource "aws_subnet" "database_b" {
  vpc_id            = aws_vpc.infrapilot.id
  cidr_block        = "10.42.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]
  tags              = { Name = "infrapilot-database-b" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.infrapilot.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.infrapilot.id
  }
  tags = { Name = "infrapilot-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "app" {
  name        = "infrapilot-app"
  description = "Public HTTP health endpoint and outbound access for updates and AWS APIs"
  vpc_id      = aws_vpc.infrapilot.id

  ingress {
    description = "HTTP health endpoint"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound access"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "infrapilot-app" }
}

resource "aws_security_group" "database" {
  name        = "infrapilot-database"
  description = "MySQL access only from the InfraPilot application host"
  vpc_id      = aws_vpc.infrapilot.id

  ingress {
    description     = "MySQL from application host"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "infrapilot-database" }
}

resource "aws_db_subnet_group" "infrapilot" {
  name       = "infrapilot-database"
  subnet_ids = [aws_subnet.database_a.id, aws_subnet.database_b.id]
  tags       = { Name = "infrapilot-database" }
}

resource "aws_secretsmanager_secret" "database" {
  name                    = "infrapilot/database-credentials"
  description             = "InfraPilot RDS credentials"
  recovery_window_in_days = 0
}

resource "aws_db_instance" "infrapilot" {
  identifier                 = "infrapilot-mysql"
  engine                     = "mysql"
  engine_version             = "8.4.11"
  instance_class             = var.db_instance_class
  allocated_storage          = 20
  storage_type               = "gp3"
  storage_encrypted          = true
  db_name                    = "infrapilot"
  username                   = var.db_username
  password                   = var.db_password
  port                       = 3306
  db_subnet_group_name       = aws_db_subnet_group.infrapilot.name
  vpc_security_group_ids     = [aws_security_group.database.id]
  publicly_accessible        = false
  multi_az                   = false
  backup_retention_period    = 1
  auto_minor_version_upgrade = true
  deletion_protection        = false
  skip_final_snapshot        = true
  apply_immediately          = true

  tags = { Name = "infrapilot-mysql" }
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

resource "aws_ecr_repository" "api" {
  name                 = "infrapilot-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = { Name = "infrapilot-api" }
}

resource "aws_iam_role" "app" {
  name = "infrapilot-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "app_access" {
  name = "infrapilot-app-runtime"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.database.arn
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = aws_ecr_repository.api.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "infrapilot-ec2-profile"
  role = aws_iam_role.app.name
}

resource "aws_instance" "app" {
  count                       = var.deploy_app ? 1 : 0
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.app_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.app.name
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = 12
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    region          = var.region
    ecr_repository  = aws_ecr_repository.api.repository_url
    image_uri       = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
    database_secret = aws_secretsmanager_secret.database.arn
    database_host   = aws_db_instance.infrapilot.address
    database_name   = aws_db_instance.infrapilot.db_name
    database_port   = aws_db_instance.infrapilot.port
  })

  depends_on = [
    aws_iam_role_policy_attachment.ssm,
    aws_iam_role_policy.app_access,
    aws_secretsmanager_secret_version.database
  ]

  tags = { Name = "infrapilot-app" }
}
