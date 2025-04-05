import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from config import constants, schemas
from google.cloud import bigquery
from tenacity import retry, stop_after_attempt, wait_exponential
from services.gcs_uploader import GCSUploader
from services.api_client import LuftdatenAPIClient
from services.bigquery_client import BigQueryClient
from utils.time_utils import parse_airquality_timestamp

class MeasuresProcessor:
    def __init__(self, api_client: LuftdatenAPIClient,
                 gcs: GCSUploader, bq: BigQueryClient):
        self.api = api_client
        self.gcs = gcs
        self.bq = bq
        self.utc_now = datetime.now(timezone.utc)
        self.station_id = constants.CONFIG["station_id"]

    def process_measures(self) -> int:
        """Orchestrate measures processing pipeline"""
        components = self._get_valid_components()
        return sum(
            self._process_component(component)
            for component in components
        )

    def _get_valid_components(self) -> List[Dict[str, Any]]:
        """Get components with availability checks"""
        return [
            comp for comp in self._fetch_components()
            if self._component_available(comp['id'])
        ]

    def _fetch_components(self) -> List[Dict[str, Any]]:
        """Retrieve and transform components from API"""
        raw_components = self.api.get_components()
        return [
            {"id": int(values[0]), "code": key, "unit": values[3]}
            for key, values in raw_components.items()
            if key not in constants.CONFIG["excluded_component_keys"]
        ]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
    def _component_available(self, component_id: int) -> bool:
        """Check if component has data for our station"""
        try:
            test_data = self.api.get_measures(component_id, self.station_id)
            return bool(test_data.get('data', {}).get(str(self.station_id)))
        except Exception as e:
            logging.warning(f"Component check failed: {component_id} - {str(e)}")
            return False

    def _process_component(self, component: Dict[str, Any]) -> int:
        """Process individual component"""
        try:
            measures = self.api.get_measures(component['id'], self.station_id)
            self._upload_raw_measures(component, measures)
            self._transform_and_load(component, measures)
            return 1
        except Exception as e:
            logging.error(f"Failed processing {component['code']}: {str(e)}")
            return 0

    def _upload_raw_measures(self, component: Dict[str, Any],
                            measures: Dict[str, Any]) -> None:
        """Upload raw measures to GCS"""
        blob_path = (
            f"raw/station_id={self.station_id}/"
            f"component_id={component['id']}/"
            f"year={self.utc_now.year}/month={self.utc_now.month:02}/"
            f"{self.utc_now.isoformat()}.json"
        )
        self.gcs.upload_json(measures, blob_path)

    def _transform_and_load(self, component: Dict[str, Any],
                           measures: Dict[str, Any]) -> None:
        """Transform and load measures data"""
        rows = []
        station_data = measures.get('data', {}).get(str(self.station_id), {})
        
        for measure_ts, values in station_data.items():
            try:
                row = self._create_measure_row(component, measure_ts, values)
                rows.append(row)
            except (ValueError, KeyError) as e:
                logging.error(f"Skipping invalid measure: {str(e)}")

        if rows:
            self.bq.load_table(
                rows=rows,
                table_id="raw_measures",
                schema=schemas.RAW_MEASURES_SCHEMA,
                write_disposition="WRITE_APPEND"
            )

    def _create_measure_row(self, component: Dict[str, Any],
                           measure_ts: str, values: list) -> Dict[str, Any]:
        """Create a single measure row with validation"""
        if component['id'] != values[0]:
            raise ValueError(f"Component ID mismatch: {component['id']} vs {values[0]}")

        return {
            "station_id": self.station_id,
            "measure_start_time": parse_airquality_timestamp(measure_ts).isoformat(),
            "component_id": values[0],
            "scope_id": values[1],
            "value": values[2],
            "measure_end_time": parse_airquality_timestamp(values[3]).isoformat(),
            "index": str(values[4]) if values[4] is not None else None
        }