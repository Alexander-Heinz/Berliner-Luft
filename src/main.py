import logging
import os
import json
from datetime import datetime, timezone
import traceback
from flask import jsonify
from google.cloud import bigquery
from api_client import LuftdatenAPIClient
from gcs_uploader import GCSUploader
from dotenv import load_dotenv
load_dotenv()


def load_to_bigquery(measures_data: dict, component_id: int, station_id: int) -> None:
    """Transform and load measures data to BigQuery"""
    bq = bigquery.Client()
    table_ref = bq.dataset("airquality").table("raw_measures")
    
    # Extract station ID from the first key in 'data'
    station_id_data = int(next(iter(measures_data['data'].keys())))
    if station_id_data != station_id:
        raise ValueError(f"Station ID mismatch: expected {station_id}, got {station_id_data}")
    
    rows = []
    for measure_ts, values in measures_data['data'][str(station_id)].items():
        try:
            start_dt = datetime.strptime(measure_ts, "%Y-%m-%d %H:%M:%S").isoformat()
            end_dt = datetime.strptime(values[3], "%Y-%m-%d %H:%M:%S").isoformat()
        except Exception as e:
            logging.error(f"Invalid timestamp format: {measure_ts} | {values[3]}")
            continue


        if component_id != values[0]:
            raise ValueError(
                f"Component ID mismatch: expected {component_id}, got {values[0]}"
            )
        print(f"Processing measure for component {component_id} at station {station_id}")
        print(start_dt, end_dt)
        rows.append({
            "station_id": station_id,
            "measure_start_time": start_dt,
            "component_id": values[0],
            "scope_id": values[1],
            "value": values[2],  # Handles null -> FLOAT conversion
            "measure_end_time": end_dt,
            "index": str(values[4]) if values[4] is not None else None
        })

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("station_id", "INTEGER"),
            bigquery.SchemaField("measure_start_time", "TIMESTAMP"),
            bigquery.SchemaField("component_id", "INTEGER"),
            bigquery.SchemaField("scope_id", "INTEGER"),
            bigquery.SchemaField("value", "FLOAT"),
            bigquery.SchemaField("measure_end_time", "TIMESTAMP"),
            bigquery.SchemaField("index", "STRING")
        ],
        write_disposition="WRITE_APPEND"
    )
    
    load_job = bq.load_table_from_json(rows, table_ref, job_config=job_config)
    return load_job.result()

def main(request):
    """HTTP Cloud Function entry point"""
    api = LuftdatenAPIClient()
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    gcs = GCSUploader(bucket_name)
    STATION_ID = 175
    UTC_NOW = datetime.now(timezone.utc)

    try:
        # 1. Upload dimension tables
        dimension_entities = ['components', 'stations', 'scopes']
        for entity in dimension_entities:
            data = getattr(api, f"get_{entity}")()
            blob_name = (
                f"dimensions/{entity}/"
                f"{UTC_NOW.strftime('%Y%m%d')}/"
                f"{entity}_{UTC_NOW.isoformat()}.json"
            )
            gcs.upload_json(data, blob_name)

        # 2. Process measures for each component
        components = [
            {"id": int(values[0]), "code": key, "unit": values[3]}
            for key, values in api.get_components().items()
            if key not in ["count", "indices"]
        ]

        for component in components:
            try:
                # Fetch measures for this component
                measures = api.get_measures(
                    component_id=component['id'],
                    station_id=STATION_ID
                )

                # Store raw JSON with component/station partitioning
                blob_path = (
                    f"raw/station_id={STATION_ID}/"
                    f"component_id={component['id']}/"
                    f"year={UTC_NOW.year}/month={UTC_NOW.month:02}/"
                    f"{UTC_NOW.isoformat()}.json"
                )
                gcs.upload_json(measures, blob_path)

                # Transform and load to BigQuery
                load_to_bigquery(
                    measures_data=measures,
                    component_id=component['id'],
                    station_id=STATION_ID
                )

            except Exception as component_error:
                logging.error(f"Failed processing {component['code']}: {str(component_error)}")
                continue

        return jsonify({
            "status": "success",
            "components_processed": len(components)
        }), 200

    except Exception as main_error:
        logging.exception("Critical error in main function:")
        return jsonify({
            "status": "error",
            "message": str(main_error),
            "stack_trace": traceback.format_exc()
        }), 500
