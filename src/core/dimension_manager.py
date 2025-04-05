import logging
from datetime import datetime, timezone
from typing import Dict, Any
from google.cloud import bigquery
from config import constants, schemas
from core.data_transformer import DataTransformer
from services.gcs_uploader import GCSUploader
from services.api_client import LuftdatenAPIClient
from services.bigquery_client import BigQueryClient

class DimensionManager:
    def __init__(self, api_client: LuftdatenAPIClient, 
                 gcs: GCSUploader, bq: BigQueryClient):
        self.api = api_client
        self.gcs = gcs
        self.bq = bq
        self.utc_now = datetime.now(timezone.utc)

    def process_dimensions(self) -> None:
        """Orchestrate dimension processing pipeline"""
        for entity in constants.CONFIG["dimension_tables"]:
            try:
                data = self._fetch_dimension_data(entity)
                self._upload_to_gcs(entity, data)
                self._load_to_bigquery(entity, data)
            except Exception as e:
                logging.error(f"Dimension processing failed for {entity}: {str(e)}")
                
    def _fetch_dimension_data(self, entity: str) -> Dict[str, Any]:
        """Retrieve data from API"""
        return getattr(self.api, f"get_{entity}")()

    def _upload_to_gcs(self, entity: str, data: Dict[str, Any]) -> None:
        """Upload raw dimension data to GCS"""
        blob_name = (
            f"dimensions/{entity}/"
            f"{self.utc_now.strftime('%Y%m%d')}/"
            f"{entity}_{self.utc_now.isoformat()}.json"
        )
        self.gcs.upload_json(data, blob_name)

    def _load_to_bigquery(self, entity: str, data: Dict[str, Any]) -> None:
        """Transform and load dimension data to BigQuery"""
        transformer = getattr(DataTransformer, f"transform_{entity}")
        rows = transformer(data)
        
        if not rows:
            logging.warning(f"No rows to load for {entity}")
            return

        self.bq.load_table(
            rows=rows,
            table_id=f"dim_{entity}",
            schema=schemas.DIMENSION_SCHEMAS[entity],
            write_disposition="WRITE_TRUNCATE"
        )