terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# Variables
variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "project_id" {
  description = "Project identifier"
  type        = string
}

variable "ssh_key_name" {
  description = "AWS key pair name for SSH access"
  type        = string
  default     = ""
}

variable "systems" {
  description = "System configurations for instances"
  type = map(object({
    instance_type = string
    disk_size     = number
    disk_type     = string
    label         = optional(string, "")
    node_count    = optional(number, 1)
  }))
  default = {}
}

variable "required_ports" {
  description = "Required ports for all systems in the benchmark"
  type        = map(number)
  default     = {}
}

variable "allow_external_database_access" {
  description = "Allow external access to database ports (use with caution)"
  type        = bool
  default     = false
}

# Data sources
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC and networking
resource "aws_vpc" "benchmark" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "benchmark-${var.project_id}"
    Project = var.project_id
  }
}

resource "aws_internet_gateway" "benchmark" {
  vpc_id = aws_vpc.benchmark.id

  tags = {
    Name    = "benchmark-${var.project_id}-igw"
    Project = var.project_id
  }
}

resource "aws_subnet" "benchmark" {
  vpc_id                  = aws_vpc.benchmark.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name    = "benchmark-${var.project_id}-subnet"
    Project = var.project_id
  }
}

resource "aws_route_table" "benchmark" {
  vpc_id = aws_vpc.benchmark.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.benchmark.id
  }

  tags = {
    Name    = "benchmark-${var.project_id}-rt"
    Project = var.project_id
  }
}

resource "aws_route_table_association" "benchmark" {
  subnet_id      = aws_subnet.benchmark.id
  route_table_id = aws_route_table.benchmark.id
}

# Security group
resource "aws_security_group" "benchmark" {
  name_prefix = "benchmark-${var.project_id}"
  vpc_id      = aws_vpc.benchmark.id

  # SSH access
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow ALL TCP traffic between nodes in the same security group
  # This is required for cluster communication (Exasol c4, ClickHouse distributed queries)
  ingress {
    description = "Inter-node TCP communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  # Allow ALL UDP traffic between nodes in the same security group
  # This is required for cluster communication (Exasol cluster coordination)
  ingress {
    description = "Inter-node UDP communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "udp"
    self        = true
  }

  # Dynamic database ports from system requirements
  dynamic "ingress" {
    for_each = var.required_ports
    content {
      description = ingress.key
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["10.0.0.0/16"]
    }
  }

  # Allow all required ports from same security group (for health checks from same machine)
  dynamic "ingress" {
    for_each = var.required_ports
    content {
      description = "${ingress.key}_self"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      self        = true
    }
  }

  # Optional external access to database ports (use with caution)
  dynamic "ingress" {
    for_each = var.allow_external_database_access ? var.required_ports : {}
    content {
      description = "${ingress.key}_external"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "benchmark-${var.project_id}-sg"
    Project = var.project_id
  }
}

# Flatten systems into individual nodes
# This creates a list where each element represents a single node
# For multinode systems (node_count > 1), creates multiple entries
locals {
  system_nodes = flatten([
    for system_key, system_config in var.systems : [
      for node_idx in range(system_config.node_count) : {
        system_key    = system_key
        node_idx      = node_idx
        node_key      = system_config.node_count > 1 ? "${system_key}-node${node_idx}" : system_key
        instance_type = system_config.instance_type
        disk_size     = system_config.disk_size
        disk_type     = system_config.disk_type
        label         = system_config.label
        node_count    = system_config.node_count
      }
    ]
  ])

  # Convert to map for easier access in resources
  system_nodes_map = { for node in local.system_nodes : node.node_key => node }
}

# Generic system instances and storage
# Only create EBS volumes when disk_type is not "local"
resource "aws_ebs_volume" "system_data" {
  for_each = { for k, v in local.system_nodes_map : k => v if v.disk_type != "local" }

  availability_zone = data.aws_availability_zones.available.names[0]
  type              = each.value.disk_type
  size              = each.value.disk_size
  iops              = each.value.disk_type == "gp3" ? min(16000, max(3000, each.value.disk_size * 3)) : null
  throughput        = each.value.disk_type == "gp3" ? min(1000, max(125, each.value.disk_size / 4)) : null
  encrypted         = true

  tags = merge({
    Name    = "benchmark-${var.project_id}-${each.key}-data"
    Project = var.project_id
    System  = each.value.system_key
    Node    = each.value.node_idx
  }, each.value.label != "" ? {
    Label = each.value.label
  } : {})
}

resource "aws_instance" "system" {
  for_each = local.system_nodes_map

  ami                    = data.aws_ami.ubuntu.id
  instance_type          = each.value.instance_type
  subnet_id              = aws_subnet.benchmark.id
  vpc_security_group_ids = [aws_security_group.benchmark.id]
  key_name               = var.ssh_key_name != "" ? var.ssh_key_name : null

  root_block_device {
    volume_type = "gp3"
    volume_size = 50
    encrypted   = true
  }

  # User data script handles only infrastructure setup (Docker, Python, tools)
  # Storage setup is handled by benchmark system classes
  user_data = base64encode(file("${path.module}/user_data.sh"))

  tags = merge({
    Name      = "benchmark-${var.project_id}-${each.key}"
    Project   = var.project_id
    System    = each.value.system_key
    Node      = each.value.node_idx
    NodeCount = each.value.node_count
  }, each.value.label != "" ? {
    Label = each.value.label
  } : {})
}

resource "aws_volume_attachment" "system_data" {
  for_each = { for k, v in local.system_nodes_map : k => v if v.disk_type != "local" }

  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.system_data[each.key].id
  instance_id = aws_instance.system[each.key].id
}

# Generic outputs for all systems
# Group nodes by system name for multinode support
output "system_instance_ids" {
  description = "Map of system names to EC2 instance IDs (or list of IDs for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      aws_instance.system["${system_key}-node${node_idx}"].id
    ] : [aws_instance.system[system_key].id]
  }
}

output "system_public_ips" {
  description = "Map of system names to public IP addresses (or list of IPs for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      aws_instance.system["${system_key}-node${node_idx}"].public_ip
    ] : [aws_instance.system[system_key].public_ip]
  }
}

output "system_private_ips" {
  description = "Map of system names to private IP addresses (or list of IPs for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      aws_instance.system["${system_key}-node${node_idx}"].private_ip
    ] : [aws_instance.system[system_key].private_ip]
  }
}

output "system_ssh_commands" {
  description = "Map of system names to SSH commands (or list of commands for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      "ssh ubuntu@${aws_instance.system["${system_key}-node${node_idx}"].public_ip}"
    ] : ["ssh ubuntu@${aws_instance.system[system_key].public_ip}"]
  }
}

