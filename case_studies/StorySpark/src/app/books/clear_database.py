from fastapi import APIRouter
from app.books.helpers.bigquery_client_helper import get_bigquery_client

router = APIRouter()

@router.delete("/books", response_model=None, operation_id="ClearDatabase")
async def clear_database():
    """
    Clears all tables
    """
    bigquery_client_helper = get_bigquery_client()

    transaction_script = f"""
    BEGIN TRANSACTION;

    TRUNCATE TABLE `{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}`;
    TRUNCATE TABLE `{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}`;

    COMMIT TRANSACTION;
    """

    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=None)
        # Waiting on the result means we wait for the COMMIT to finish
        rows = query_job.result()
        for row in rows:
            print(row)

    except Exception as e:
        print(f"Transaction failed and was rolled back: {e}")
        raise

    return

