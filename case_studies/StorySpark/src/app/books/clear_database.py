import logging
from fastapi import APIRouter, Depends
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from app.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("app-log")


@router.delete("/books", response_model=None, operation_id="ClearDatabase")
async def clear_database(
    current_user: dict = Depends(get_current_user)
    ):
    """
    Clears all tables (admin-only operation restricted to allowed users).
    """
    owner = current_user["email"]
    logger.info(f"ClearDatabase called by user: {owner}")

    bigquery_client_helper = get_bigquery_client()
    source_table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    embeddings_table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}"

    transaction_script = f"""
    BEGIN TRANSACTION;

    TRUNCATE TABLE `{source_table_ref}`;
    TRUNCATE TABLE `{embeddings_table_ref}`;

    COMMIT TRANSACTION;
    """

    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=None)
        # Waiting on the result means we wait for the COMMIT to finish
        query_job.result()

    except Exception as e:
        logger.error(f"ClearDatabase transaction failed and was rolled back: {e}")
        raise

    return
