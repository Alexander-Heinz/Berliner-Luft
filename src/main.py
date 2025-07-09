import logging
import traceback
from flask import jsonify
from config import constants
from core.dimension_manager import DimensionManager
from core.measures_processor import MeasuresProcessor
from services.gcs_uploader import GCSUploader
from services.api_client import LuftdatenAPIClient
from services.bigquery_client import BigQueryClient


def main(request):
    """HTTP Cloud Function entry point"""
    try:
        api = LuftdatenAPIClient()
        gcs = GCSUploader(constants.CONFIG["gcs_bucket"])
        bq = BigQueryClient(project=constants.CONFIG["project"],
                            dataset_id=constants.CONFIG["bq_dataset"])

        process_dimensions(api, gcs, bq)
        success_count = process_measures(api, gcs, bq)

        return json_success_response(success_count)
    
    except Exception as e:
        return json_error_response(e)


def process_dimensions(api, gcs, bq):
    """Process dimension tables"""
    DimensionManager(api, gcs, bq).process_dimensions()


def process_measures(api, gcs, bq) -> int:
    """Process measures data"""
    return MeasuresProcessor(api, gcs, bq).process_measures()


def json_success_response(success_count: int):
    return jsonify({
        "status": "success",
        "components_processed": success_count
    }), 200


def json_error_response(error: Exception):
    logging.exception("Critical error:")
    return jsonify({
        "status": "error",
        "message": str(error),
        "stack_trace": traceback.format_exc()
    }), 500