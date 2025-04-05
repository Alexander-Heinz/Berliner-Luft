from google.cloud import bigquery

DIMENSION_SCHEMAS = {
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

RAW_MEASURES_SCHEMA = [
    bigquery.SchemaField("station_id", "INTEGER"),
    bigquery.SchemaField("measure_start_time", "TIMESTAMP"),
    bigquery.SchemaField("component_id", "INTEGER"),
    bigquery.SchemaField("scope_id", "INTEGER"),
    bigquery.SchemaField("value", "FLOAT"),
    bigquery.SchemaField("measure_end_time", "TIMESTAMP"),
    bigquery.SchemaField("index", "STRING")
]