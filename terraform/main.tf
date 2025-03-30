terraform {
  required_providers {
    google = {
        source  = "hashicorp/google"
      version = "~> 4.0"
        # version = "6.8.0"
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
  force_destroy = true
  
#   lifecycle {
#     prevent_destroy = true
#   }
}

resource "google_storage_bucket_object" "function_source" {
  name   = "functions/function.zip"  
  bucket = google_storage_bucket.berliner_luft.name
  source = "../function.zip"
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com"  # New required service
  ])
  service = each.key
}

# BigQuery Dataset
resource "google_bigquery_dataset" "airquality" {
  dataset_id    = "airquality"
  friendly_name = "Air Quality Data"
  location      = var.region
}

# Raw Data Table
resource "google_bigquery_table" "raw_measures" {
  dataset_id = google_bigquery_dataset.airquality.dataset_id
  table_id   = "raw_measures"
  deletion_protection = false


  time_partitioning {
    type  = "DAY"
    field = "measure_start_time"
  }

  clustering = ["component_id", "station_id"]

  schema = <<EOF
[
  {"name": "station_id", "type": "INTEGER"},
  {"name": "component_id", "type": "INTEGER"},
  {"name": "measure_start_time", "type": "TIMESTAMP"},
  {"name": "scope_id", "type": "INTEGER"},
  {"name": "value", "type": "FLOAT"},
  {"name": "measure_end_time", "type": "TIMESTAMP"},
  {"name": "index", "type": "STRING"}
]
EOF
}

# Cloud Function
resource "google_cloudfunctions_function" "ingestor" {
  name                  = "airquality-ingestor"
  region                = "europe-west3"  # Supported region
  runtime               = "python310"
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.berliner_luft.name
  source_archive_object = google_storage_bucket_object.function_source.name
  trigger_http          = true
  entry_point           = "main"
  
  environment_variables = {
    GCS_BUCKET_NAME = google_storage_bucket.berliner_luft.name
  }
}

resource "google_cloud_scheduler_job" "daily_ingestion" {
  name        = "daily-airquality-ingestion"
  schedule    = "0 0 * * *"
  time_zone   = "Europe/Berlin"
  region      = "europe-west3"  # Explicit region

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.ingestor.https_trigger_url
    oidc_token {
      service_account_email = data.google_app_engine_default_service_account.default.email
      audience              = google_cloudfunctions_function.ingestor.https_trigger_url
    }
  }
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = var.project_id
  region         = "europe-west3"
  cloud_function = google_cloudfunctions_function.ingestor.name
  role           = "roles/cloudfunctions.invoker"
  member         = "serviceAccount:${data.google_app_engine_default_service_account.default.email}"
}

data "google_app_engine_default_service_account" "default" {
  project = var.project_id
}