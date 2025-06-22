from google.cloud import bigquery

DIMENSION_SCHEMAS = {
    "components": [
        bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("unit", "STRING"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    ],
    "stations": [
        bigquery.SchemaField("station_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("latitude", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("longitude", "FLOAT", mode="REQUIRED"),
    ],
    "scopes": [
        bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
    ]
}
RAW_MEASURES_SCHEMA = [
    bigquery.SchemaField("station_id", "INTEGER"),
    bigquery.SchemaField("measure_start_time", "TIMESTAMP"),
    bigquery.SchemaField("measure_end_time", "TIMESTAMP"),
    bigquery.SchemaField("component_id", "INTEGER"),
    bigquery.SchemaField("scope_id", "INTEGER"),
    bigquery.SchemaField("value", "FLOAT"),
    bigquery.SchemaField("index", "STRING")
]