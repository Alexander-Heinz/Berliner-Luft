variable "project_id" {
  description = "berliner-luft"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "europe-west3"  # Frankfurt region
}

variable "bucket_name" {
  default = "berliner-luft"
}