import datetime
import os
from typing import Dict, List
from src.api_client import LuftdatenAPIClient
from src.gcs_uploader import GCSUploader

def upload_dimension_tables(api_client: LuftdatenAPIClient, 
                          gcs_uploader: GCSUploader) -> None:
    """Upload static dimension tables to GCS"""
    dimension_entities = ['components', 'stations', 'scopes']
    
    for entity in dimension_entities:
        try:
            data = getattr(api_client, f"get_{entity}")()
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
            blob_name = f"dimensions/{entity}/{timestamp}_{entity}.json"
            
            if gcs_uploader.upload_json(data, blob_name):
                print(f"Successfully uploaded {entity} dimension")
            else:
                print(f"Failed to upload {entity} dimension")
                
        except Exception as e:
            print(f"Error processing {entity} dimension: {str(e)}")

def process_measures(api_client: LuftdatenAPIClient,
                    gcs_uploader: GCSUploader,
                    components: List[Dict],
                    station_id: int = 175) -> None:
    """Process hourly measures for all components"""
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    for component in components:
        try:
            # Get measures data
            measures = api_client.get_measures(
                component_id=component['id'],
                station_id=station_id
            )
            
            # Create partitioned path
            blob_path = (
                f"measures/"
                f"component={component['code']}/"
                f"year={current_time.year}/"
                f"month={current_time.month:02d}/"
                f"day={current_time.day:02d}/"
                f"hour={current_time.hour:02d}.json"
            )
            
            # Upload measures
            if gcs_uploader.upload_json(measures, blob_path):
                print(f"Uploaded measures for {component['code']}")
            else:
                print(f"Failed to upload measures for {component['code']}")
                
        except Exception as e:
            print(f"Error processing {component['code']}: {str(e)}")

def main():
    # Initialize clients
    api_client = LuftdatenAPIClient()
    gcs_uploader = GCSUploader(os.getenv("GCS_BUCKET_NAME"))

    # 1. Upload dimension tables
    upload_dimension_tables(api_client, gcs_uploader)

    # 2. Process measures for all components
    components_response = api_client.get_components()
    components = [
        {
            "id": int(values[0]),
            "code": values[1],
            "unit": values[3],
            "name": values[4]
        }
        for key, values in components_response.items() 
        if key not in ["count", "indices"]
    ]
    
    process_measures(api_client, gcs_uploader, components)

if __name__ == "__main__":
    main()