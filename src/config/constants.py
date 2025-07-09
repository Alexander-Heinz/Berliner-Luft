import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "station_id": 175,
    "project": "berliner-luft-dez",
    "gcs_bucket": os.getenv("GCS_BUCKET_NAME"),
    "bq_dataset": "airquality",
    "dimension_tables": ["components", "stations", "scopes"],
    "excluded_component_keys": ["count", "indices"],
    "excluded_station_keys": ["request", "count", "indices"],
    "excluded_scope_keys": ["request", "count", "indices"]
}