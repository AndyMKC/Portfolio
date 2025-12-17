import logging
import os
from google.cloud import logging as cloud_logging

def setup_cloud_logging() -> cloud_logging.Client:
    client = cloud_logging.Client(project=os.environ.get("STORYSPARK_GCP_BQ_PROJECT_ID"))
    client.setup_logging() # adds Cloud Logging handler
    # Optionally remove duplicate StreamHandler if present
    root = logging.getLogger()
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler):
            root.removeHandler(h)
    return client