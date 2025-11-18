variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "job-tracker-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "Southeast Asia"
}

variable "app_name" {
  description = "Name of the web application (must be globally unique)"
  type        = string

}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "Development"
}

variable "mysql_admin_username" {
  description = "MySQL administrator username"
  type        = string
  default     = "jobtracker_admin"
  sensitive   = true
}

variable "mysql_admin_password" {
  description = "MySQL administrator password"
  type        = string
  sensitive   = true
}

variable "mysql_database_name" {
  description = "Name of the MySQL database"
  type        = string
  default     = "job_tracker_db"
}

variable "your_ip_address" {
  description = "Your public IP address for MySQL access"
  type        = string
}