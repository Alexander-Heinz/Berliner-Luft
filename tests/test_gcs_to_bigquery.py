import os
import json
import pytest
from datetime import datetime, timezone

from google.cloud import storage, bigquery

from config import constants, schemas
from core.data_transformer import DataTransformer
from core.dimension_manager import DimensionManager
from services.gcs_uploader import GCSUploader
from services.bigquery_client import BigQueryClient
from services.api_client import LuftdatenAPIClient


@pytest.mark.integration
def test_load_components_from_gcs_to_bigquery():
    api = LuftdatenAPIClient()
    gcs = GCSUploader(bucket_name=constants.CONFIG["gcs_bucket"])
    bq = BigQueryClient(project=constants.CONFIG["project"],
                        dataset_id=constants.CONFIG["bq_dataset"])
    dim_manager = DimensionManager(api, gcs, bq)
    data = dim_manager._fetch_dimension_data("components")
    print(data)
    dim_manager._load_to_bigquery(data=data, entity="components")