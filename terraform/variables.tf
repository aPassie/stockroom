variable "project" {
  type    = string
  default = "stockroom"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2

  validation {
    condition     = var.az_count >= 2
    error_message = "EKS needs subnets in at least two availability zones."
  }
}

variable "cluster_version" {
  type    = string
  default = "1.31"
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "cluster_admin_arns" {
  type        = list(string)
  default     = []
  description = "Extra IAM users or roles that get cluster-admin, e.g. the CI deploy user"
}
