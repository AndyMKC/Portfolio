from fastapi import APIRouter, HTTPException
from google.cloud import bigquery

from app.books.bigquery_client_helper import get_bigquery_client
from app.books.add_book import add_book

router = APIRouter()

@router.post("/reset", response_model=None, operation_id="ClearAndSeedDB")
async def clear_and_seed_db(owner: str):
    # Delete all Rows
    bigquery_client_helper = get_bigquery_client()
    table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    query = f"DELETE FROM `{table_ref}` WHERE owner = @owner_param"
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("owner_param", "STRING", owner)
        ]
    )

    query_job = bigquery_client_helper.client.query(query, job_config=job_config)

    # Seed with sample data

    # TODO:  Do this for embeddings table too
