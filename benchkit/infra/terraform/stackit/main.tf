terraform {
  required_version = ">= 1.0"
  required_providers {
    stackit = {
      source  = "stackitcloud/stackit"
      version = "~> 0.2"
    }
  }
}

provider "stackit" {
  default_region = var.region
}

# Variables
variable "region" {
  description = "STACKIT region"
  type        = string
  default     = "eu01"
}

variable "stackit_project_id" {
  description = "STACKIT project ID (UUID)"
  type        = string
}

variable "stackit_image_id" {
  description = "STACKIT boot image ID (UUID, e.g. Ubuntu 22.04)"
  type        = string
}

variable "stackit_availability_zone" {
  description = "STACKIT availability zone"
  type        = string
  default     = "eu01-1"
}

variable "project_id" {
  description = "Benchmark project identifier (used for resource naming)"
  type        = string
}

variable "ssh_key_name" {
  description = "Name for the SSH key pair"
  type        = string
  default     = ""
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
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

# Unused on STACKIT but accepted for compatibility with the shared var-building code
variable "availability_zone_index" {
  description = "Unused on STACKIT (kept for interface compatibility)"
  type        = number
  default     = 0
}

# SSH key pair
resource "stackit_key_pair" "benchmark" {
  count      = var.ssh_key_name != "" ? 1 : 0
  name       = var.ssh_key_name
  public_key = var.ssh_public_key_path != "" ? chomp(file(var.ssh_public_key_path)) : ""
}

# Network
resource "stackit_network" "benchmark" {
  project_id         = var.stackit_project_id
  name               = "benchmark-${local.safe_project_id}"
  ipv4_nameservers   = ["8.8.8.8", "8.8.4.4"]
  ipv4_prefix_length = 24
  routed             = true
}

# Security group
resource "stackit_security_group" "benchmark" {
  project_id = var.stackit_project_id
  name       = "benchmark-${local.safe_project_id}"
  stateful   = true
}

# SSH access rule
resource "stackit_security_group_rule" "ssh" {
  project_id        = var.stackit_project_id
  security_group_id = stackit_security_group.benchmark.security_group_id
  direction         = "ingress"
  ether_type        = "IPv4"
  protocol = {
    name = "tcp"
  }
  port_range = {
    min = 22
    max = 22
  }
}

# Allow ALL TCP traffic between nodes in the same security group
# Note: omitting port_range means "all ports" — specifying 1-65535 explicitly
# triggers a provider bug where the API normalizes it to null.
resource "stackit_security_group_rule" "internode_tcp" {
  project_id              = var.stackit_project_id
  security_group_id       = stackit_security_group.benchmark.security_group_id
  direction               = "ingress"
  ether_type              = "IPv4"
  remote_security_group_id = stackit_security_group.benchmark.security_group_id
  protocol = {
    name = "tcp"
  }
}

# Allow ALL UDP traffic between nodes in the same security group
resource "stackit_security_group_rule" "internode_udp" {
  project_id              = var.stackit_project_id
  security_group_id       = stackit_security_group.benchmark.security_group_id
  direction               = "ingress"
  ether_type              = "IPv4"
  remote_security_group_id = stackit_security_group.benchmark.security_group_id
  protocol = {
    name = "udp"
  }
}

# Dynamic database port rules (VPC-internal access)
resource "stackit_security_group_rule" "db_ports" {
  for_each = var.required_ports

  project_id        = var.stackit_project_id
  security_group_id = stackit_security_group.benchmark.security_group_id
  direction         = "ingress"
  ether_type        = "IPv4"
  protocol = {
    name = "tcp"
  }
  port_range = {
    min = each.value
    max = each.value
  }
  ip_range = stackit_network.benchmark.ipv4_prefix
}

# Optional external access to database ports
resource "stackit_security_group_rule" "db_ports_external" {
  for_each = var.allow_external_database_access ? var.required_ports : {}

  project_id        = var.stackit_project_id
  security_group_id = stackit_security_group.benchmark.security_group_id
  direction         = "ingress"
  ether_type        = "IPv4"
  protocol = {
    name = "tcp"
  }
  port_range = {
    min = each.value
    max = each.value
  }
}

# Allow all outbound traffic
resource "stackit_security_group_rule" "egress" {
  project_id        = var.stackit_project_id
  security_group_id = stackit_security_group.benchmark.security_group_id
  direction         = "egress"
  ether_type        = "IPv4"
}

# STACKIT resource names must not contain underscores — sanitize identifiers
locals {
  safe_project_id = replace(var.project_id, "_", "-")
}

# Flatten systems into individual nodes (same logic as AWS)
locals {
  system_nodes = flatten([
    for system_key, system_config in var.systems : [
      for node_idx in range(system_config.node_count) : {
        system_key    = system_key
        node_idx      = node_idx
        node_key      = system_config.node_count > 1 ? "${system_key}-node${node_idx}" : system_key
        safe_node_key = replace(system_config.node_count > 1 ? "${system_key}-node${node_idx}" : system_key, "_", "-")
        instance_type = system_config.instance_type
        disk_size     = system_config.disk_size
        disk_type     = system_config.disk_type
        label         = system_config.label
        node_count    = system_config.node_count
      }
    ]
  ])

  system_nodes_map = { for node in local.system_nodes : node.node_key => node }
}

# Boot volumes (one per node)
resource "stackit_volume" "boot" {
  for_each = local.system_nodes_map

  project_id        = var.stackit_project_id
  name              = "benchmark-${local.safe_project_id}-${each.value.safe_node_key}-boot"
  availability_zone = var.stackit_availability_zone
  size              = 64
  performance_class = "storage_premium_perf1"

  source = {
    type = "image"
    id   = var.stackit_image_id
  }

  labels = merge({
    project = var.project_id
    system  = each.value.system_key
    node    = tostring(each.value.node_idx)
  }, each.value.label != "" ? {
    label = each.value.label
  } : {})
}

# Data volumes (only when disk_type is not "local" and not "none")
resource "stackit_volume" "data" {
  for_each = { for k, v in local.system_nodes_map : k => v if v.disk_type != "local" && v.disk_type != "none" }

  project_id        = var.stackit_project_id
  name              = "benchmark-${local.safe_project_id}-${each.value.safe_node_key}-data"
  availability_zone = var.stackit_availability_zone
  size              = each.value.disk_size
  performance_class = each.value.disk_type

  labels = merge({
    project = var.project_id
    system  = each.value.system_key
    node    = tostring(each.value.node_idx)
  }, each.value.label != "" ? {
    label = each.value.label
  } : {})
}

# Network interfaces (one per node, created before servers)
resource "stackit_network_interface" "system" {
  for_each = local.system_nodes_map

  project_id         = var.stackit_project_id
  network_id         = stackit_network.benchmark.network_id
  security_group_ids = [stackit_security_group.benchmark.security_group_id]
}

# Servers (with network interfaces configured inline)
resource "stackit_server" "system" {
  for_each = local.system_nodes_map

  project_id        = var.stackit_project_id
  name              = "benchmark-${local.safe_project_id}-${each.value.safe_node_key}"
  availability_zone = var.stackit_availability_zone
  machine_type      = each.value.instance_type
  keypair_name      = var.ssh_key_name != "" ? stackit_key_pair.benchmark[0].name : null

  boot_volume = {
    source_type = "volume"
    source_id   = stackit_volume.boot[each.key].volume_id
  }

  network_interfaces = [
    stackit_network_interface.system[each.key].network_interface_id
  ]

  user_data = file("${path.module}/user_data.sh")

  labels = merge({
    project    = var.project_id
    system     = each.value.system_key
    node       = tostring(each.value.node_idx)
    node_count = tostring(each.value.node_count)
  }, each.value.label != "" ? {
    label = each.value.label
  } : {})
}

# Public IPs (one per node)
resource "stackit_public_ip" "system" {
  for_each = local.system_nodes_map

  project_id           = var.stackit_project_id
  network_interface_id = stackit_network_interface.system[each.key].network_interface_id

  depends_on = [stackit_server.system]
}

# Attach data volumes to servers
resource "stackit_server_volume_attach" "data" {
  for_each = { for k, v in local.system_nodes_map : k => v if v.disk_type != "local" && v.disk_type != "none" }

  project_id = var.stackit_project_id
  server_id  = stackit_server.system[each.key].server_id
  volume_id  = stackit_volume.data[each.key].volume_id
}

# Outputs (identical structure to AWS module)
output "system_instance_ids" {
  description = "Map of system names to server IDs (or list of IDs for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      stackit_server.system["${system_key}-node${node_idx}"].server_id
    ] : [stackit_server.system[system_key].server_id]
  }
}

output "system_public_ips" {
  description = "Map of system names to public IP addresses (or list of IPs for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      stackit_public_ip.system["${system_key}-node${node_idx}"].ip
    ] : [stackit_public_ip.system[system_key].ip]
  }
}

output "system_private_ips" {
  description = "Map of system names to private IP addresses (or list of IPs for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      stackit_network_interface.system["${system_key}-node${node_idx}"].ipv4
    ] : [stackit_network_interface.system[system_key].ipv4]
  }
}

output "system_ssh_commands" {
  description = "Map of system names to SSH commands (or list of commands for multinode)"
  value = {
    for system_key, system_config in var.systems :
    system_key => system_config.node_count > 1 ? [
      for node_idx in range(system_config.node_count) :
      "ssh ubuntu@${stackit_public_ip.system["${system_key}-node${node_idx}"].ip}"
    ] : ["ssh ubuntu@${stackit_public_ip.system[system_key].ip}"]
  }
}
