import logging
import os
from datetime import datetime, timezone
import traceback
from typing import Dict, Any, List
from flask import jsonify
from google.cloud import bigquery
from api_client import LuftdatenAPIClient
from gcs_uploader import GCSUploader
from bigquery_client import BigQueryClient
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Constants
CONFIG = {
    "station_id": 175,
    "gcs_bucket": os.getenv("GCS_BUCKET_NAME"),
    "bq_dataset": "airquality",
    "dimension_tables": ["components", "stations", "scopes"]
}

# Type aliases
ApiResponse = Dict[str, Any]

class DataTransformer:
    """Handles data transformation logic for different entity types"""
    
    @staticmethod
    def transform_components(data: ApiResponse) -> List[Dict[str, Any]]:
        return [
            {
                "id": int(values[0]),
                "code": code,
                "name": values[1],
                "description": values[2],
                "unit": values[3]
            }
            for code, values in data.items()
            if code not in ["count", "indices"]
        ]

    @staticmethod
    def transform_stations(data: ApiResponse) -> List[Dict[str, Any]]:
        return [
            {
                "station_id": int(station_id),
                "name": values[0],
                "latitude": float(values[1]),
                "longitude": float(values[2])
            }
            for station_id, values in data.items()
            if station_id != ["request", "count", "indices"]
            and station_id.isdigit() 
        ]

    @staticmethod
    def transform_scopes(data: ApiResponse) -> List[Dict[str, Any]]:
        return [
            {
                "scope_id": int(scope_id),
                "name": values[0],
                "description": values[1]
            }
            for scope_id, values in data.items()
            if scope_id not in ["request", "count", "indices"]  
            and scope_id.isdigit() 
        ]

class DimensionManager:
    """Handles dimension data processing pipeline"""
    
    def __init__(self, api_client: LuftdatenAPIClient, gcs: GCSUploader, bq: BigQueryClient):
        self.api = api_client
        self.gcs = gcs
        self.bq = bq
        self.utc_now = datetime.now(timezone.utc)

    def process_dimensions(self) -> None:
        """Process all dimension entities"""
        for entity in CONFIG["dimension_tables"]:
            try:
                data = getattr(self.api, f"get_{entity}")()
                self._upload_to_gcs(entity, data)
                self._load_to_bigquery(entity, data)
            except Exception as e:
                logging.error(f"Failed processing {entity}: {str(e)}")
                continue

    def _upload_to_gcs(self, entity: str, data: ApiResponse) -> None:
        """Upload raw dimension data to GCS"""
        blob_name = (
            f"dimensions/{entity}/"
            f"{self.utc_now.strftime('%Y%m%d')}/"
            f"{entity}_{self.utc_now.isoformat()}.json"
        )
        self.gcs.upload_json(data, blob_name)

    def _load_to_bigquery(self, entity: str, data: ApiResponse) -> None:
        """Transform and load dimension data to BigQuery"""
        transformer = getattr(DataTransformer, f"transform_{entity}")
        rows = transformer(data)
        
        schema_map = {
            "components": [
                bigquery.SchemaField("id", "INTEGER"),
                bigquery.SchemaField("code", "STRING"),
                bigquery.SchemaField("name", "STRING"),
                bigquery.SchemaField("description", "STRING"),
                bigquery.SchemaField("unit", "STRING"),
            ],
            "stations": [
                bigquery.SchemaField("station_id", "INTEGER"),
                bigquery.SchemaField("name", "STRING"),
                bigquery.SchemaField("latitude", "FLOAT"),
                bigquery.SchemaField("longitude", "FLOAT"),
            ],
            "scopes": [
                bigquery.SchemaField("scope_id", "INTEGER"),
                bigquery.SchemaField("name", "STRING"),
                bigquery.SchemaField("description", "STRING"),
            ]
        }
        
        self.bq.load_table(
            rows=rows,
            table_id=f"dim_{entity}",
            schema=schema_map[entity],
            write_disposition="WRITE_TRUNCATE"
        )

class MeasuresProcessor:
    """Handles measures data processing pipeline"""
    
    def __init__(self, api_client: LuftdatenAPIClient, gcs: GCSUploader, bq: BigQueryClient):
        self.api = api_client
        self.gcs = gcs
        self.bq = bq
        self.utc_now = datetime.now(timezone.utc)
        self.station_id = CONFIG["station_id"]

    def _component_available(self, component_id: int) -> bool:
        """Check if component has data for our station"""
        try:
            test_data = self.api.get_measures(
                component_id=component_id,
                station_id=self.station_id
            )
            return bool(test_data.get('data', {}).get(str(self.station_id)))
        except Exception as e:
            logging.warning(f"Component check failed for {component_id}: {str(e)}")
            return False

    def process_measures(self) -> int:
        """Process all components' measures data"""
        components = [
            {"id": int(values[0]), "code": key, "unit": values[3]}
            for key, values in self.api.get_components().items()
            if key not in ["count", "indices"]
        ]

        available_components = [
        comp for comp in components
        if self._component_available(comp['id'])
    ]

        success_count = 0
        for component in available_components:
            try:
                measures = self.api.get_measures(
                    component_id=component['id'],
                    station_id=self.station_id
                )
                self._upload_raw_measures(component, measures)
                self._load_measures_to_bq(component, measures)
                success_count += 1
            except Exception as e:
                logging.error(f"Failed processing {component['code']}: {str(e)}")
                continue
        return success_count

    def _upload_raw_measures(self, component: Dict[str, Any], measures: ApiResponse) -> None:
        """Upload raw measures data to GCS"""
        blob_path = (
            f"raw/station_id={self.station_id}/"
            f"component_id={component['id']}/"
            f"year={self.utc_now.year}/month={self.utc_now.month:02}/"
            f"{self.utc_now.isoformat()}.json"
        )
        self.gcs.upload_json(measures, blob_path)


    def _load_measures_to_bq(self, component: Dict[str, Any], measures: ApiResponse) -> None:
        """Transform and load measures data to BigQuery"""
        rows = []
        for measure_ts, values in measures['data'][str(self.station_id)].items():
            try:
                # Fix 24:00:00 timestamps
                if measure_ts.endswith(" 24:00:00"):
                    measure_ts = measure_ts.replace(" 24:00:00", " 00:00:00")
                    new_date = datetime.strptime(measure_ts, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
                    measure_ts = new_date.strftime("%Y-%m-%d %H:%M:%S")
                
                end_time = values[3]
                # Fix 24:00:00 timestamps
                if end_time.endswith(" 24:00:00"):
                    end_time = end_time.replace(" 24:00:00", " 00:00:00")
                    new_date = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") + timedelta(days=1)
                    end_time = new_date.strftime("%Y-%m-%d %H:%M:%S")

                start_dt = datetime.strptime(measure_ts, "%Y-%m-%d %H:%M:%S").isoformat()
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").isoformat()
            except ValueError as e:
                logging.error(f"Invalid timestamp {measure_ts}: {str(e)}")
                continue

            if component['id'] != values[0]:
                raise ValueError(
                    f"Component ID mismatch: expected {component['id']}, got {values[0]}"
                )

            rows.append({
                "station_id": self.station_id,
                "measure_start_time": start_dt,
                "component_id": values[0],
                "scope_id": values[1],
                "value": values[2],
                "measure_end_time": end_dt,
                "index": str(values[4]) if values[4] is not None else None
            })

        schema = [
            bigquery.SchemaField("station_id", "INTEGER"),
            bigquery.SchemaField("measure_start_time", "TIMESTAMP"),
            bigquery.SchemaField("component_id", "INTEGER"),
            bigquery.SchemaField("scope_id", "INTEGER"),
            bigquery.SchemaField("value", "FLOAT"),
            bigquery.SchemaField("measure_end_time", "TIMESTAMP"),
            bigquery.SchemaField("index", "STRING")
        ]
        
        self.bq.load_table(
            rows=rows,
            table_id="raw_measures",
            schema=schema,
            write_disposition="WRITE_APPEND"
        )

def main(request):
    """HTTP Cloud Function entry point"""
    try:
        # Initialize clients
        api = LuftdatenAPIClient()
        gcs = GCSUploader(CONFIG["gcs_bucket"])
        bq = BigQueryClient(CONFIG["bq_dataset"])

        # Process dimensions
        dimension_manager = DimensionManager(api, gcs, bq)
        dimension_manager.process_dimensions()

        # Process measures
        measures_processor = MeasuresProcessor(api, gcs, bq)
        success_count = measures_processor.process_measures()

        return jsonify({
            "status": "success",
            "components_processed": success_count
        }), 200

    except Exception as e:
        logging.exception("Critical error in main function:")
        return jsonify({
            "status": "error",
            "message": str(e),
            "stack_trace": traceback.format_exc()
        }), 500