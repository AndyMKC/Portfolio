from google.cloud import bigquery
import os

class BigQueryClientHelper:
    project_id: str
    dataset_id: str
    source_table_id: str
    embeddings_table_id: str
    client: bigquery.Client

def get_bigquery_client() -> BigQueryClientHelper:
    """Creates and returns a BigQuery client using default credentials from the Environment Variables"""

    bigquery_client_helper = BigQueryClientHelper()
    bigquery_client_helper.project_id = os.environ.get("STORYSPARK_GCP_BQ_PROJECT_ID")
    bigquery_client_helper.dataset_id = os.environ.get("STORYSPARK_GCP_BQ_DATASET_ID")
    bigquery_client_helper.source_table_id = os.environ.get("STORYSPARK_GCP_BQ_SOURCE_TABLE_ID")
    bigquery_client_helper.embeddings_table_id = os.environ.get("STORYSPARK_GCP_BQ_EMBEDDINGS_TABLE_ID")
    bigquery_client_helper.client = bigquery.Client(project=bigquery_client_helper.project_id)
    
    return bigquery_client_helper