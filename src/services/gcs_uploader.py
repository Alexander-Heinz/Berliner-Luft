import json
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
import logging

logger = logging.getLogger(__name__)


class GCSUploader:
    def __init__(self, bucket_name):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
    
    def upload_json(self, data, destination_blob_name):
        """Upload JSON-serializable data directly to GCS"""
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_string(
                data=json.dumps(data),
                content_type='application/json'
            )
            logger.info(f"Uploaded {destination_blob_name} to GCS")
            # logger.info("Sample transformed record: %s", json.dumps(data))
            return True
        except GoogleAPIError as e:
            logger.error(f"GCS upload failed: {str(e)}")
            return False