# bigquery_client.py
import logging
from google.cloud import bigquery
from typing import List, Dict, Any
from google.cloud.bigquery import SchemaField

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# Set up logging configuration

class BigQueryClient:
    def __init__(self, dataset_id: str = "airquality"):
        self.client = bigquery.Client()
        self.dataset_id = dataset_id

    def load_table(
        self,
        rows: List[Dict[str, Any]],
        table_id: str,
        schema: List[SchemaField],
        write_disposition: str = "WRITE_APPEND"
    ) -> None:
        """Generic method to load data into BigQuery"""
        table_ref = self.client.dataset(self.dataset_id).table(table_id)
        
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=write_disposition
        )
        
        load_job = self.client.load_table_from_json(rows, table_ref, job_config=job_config)
        load_job.result()
        logging.info(f"Loaded {len(rows)} rows into {table_id}")