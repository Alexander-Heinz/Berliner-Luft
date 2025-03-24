terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "berliner_luft" {
  name          = "berliner-luft"
  location      = var.region
  force_destroy = false
  
  lifecycle {
    prevent_destroy = true
  }
}