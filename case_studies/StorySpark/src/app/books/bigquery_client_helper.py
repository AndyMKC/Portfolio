from urllib.request import Request
from google.cloud import bigquery
import os

class BigQueryClientHelper:
    def __init__(self, project_id, dataset_id, source_table_id, embeddings_table_id, client):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.source_table_id = source_table_id
        self.embeddings_table_id = embeddings_table_id
        self.client = client
    
    def to_dict(self):
        return {
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "source_table_id": self.source_table_id,
            "embeddings_table_id": self.embeddings_table_id,
            # intentionally omit client or include only safe metadata "client_info": {"project": getattr(self.client, "project", None)}
        }
    # project_id: str
    # dataset_id: str
    # source_table_id: str
    # embeddings_table_id: str
    # client: bigquery.Client

def get_bigquery_client() -> BigQueryClientHelper:
    """Creates and returns a BigQuery client using default credentials from the Environment Variables"""

    bigquery_client_helper = BigQueryClientHelper(project_id=os.environ.get("STORYSPARK_GCP_BQ_PROJECT_ID"),
                                                  dataset_id=os.environ.get("STORYSPARK_GCP_BQ_DATASET_ID"),
                                                  source_table_id=os.environ.get("STORYSPARK_GCP_BQ_SOURCE_TABLE_ID"),
                                                  embeddings_table_id=os.environ.get("STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID"),
                                                  client=bigquery.Client(project=os.environ.get("STORYSPARK_GCP_BQ_PROJECT_ID")))
    # bigquery_client_helper.project_id = os.environ.get("STORYSPARK_GCP_BQ_PROJECT_ID")
    # bigquery_client_helper.dataset_id = os.environ.get("STORYSPARK_GCP_BQ_DATASET_ID")
    # bigquery_client_helper.source_table_id = os.environ.get("STORYSPARK_GCP_BQ_SOURCE_TABLE_ID")
    # bigquery_client_helper.embeddings_table_id = os.environ.get("STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID")
    # bigquery_client_helper.client = bigquery.Client(project=bigquery_client_helper.project_id)
    
    return bigquery_client_helper