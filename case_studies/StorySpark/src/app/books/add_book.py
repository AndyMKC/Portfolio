from fastapi import APIRouter, Request
from datetime import datetime, timezone
from google.cloud import bigquery
import json

from app.models import AddBookRequest
from app.books.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper
from app.books.embeddings_generator import EmbeddingsGenerator

router = APIRouter()

@router.post("/books", response_model=None, status_code=201, operation_id="AddBook")
async def add_book(request: Request, add_book_request: AddBookRequest):
    """
    Inserts data into both tables atomically within a single BigQuery transaction.
    """
    bigquery_client_helper = get_bigquery_client()

    log_payload = {
        "add_book_request" : add_book_request.dict(),
        "bigquery_client_helper": bigquery_client_helper.to_dict()
    }
    cloud_logger = request.app.state.cloud_logging_client.logger("app-log")
    cloud_logger.log_struct(log_payload, severity="INFO")
    
    # We want to not have any issues where there is an entry in the source table and not something in the embeddings table so commit both changes at once
    id = f"{add_book_request.owner}:{add_book_request.isbn}"
    source_table_id = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    embeddings_table_id = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}"
    utc_now = datetime.now(timezone.utc)

    need_insertion = not id_exists(
        bigquery_client_helper=bigquery_client_helper,
        table_id=bigquery_client_helper.source_table_id,
        id_column="id",
        id=id,
    )

    if (not need_insertion):
        return
    
    # --- 1. Prepare data structures in Python ---
    
    # Determine whether we need to create embeddings
    need_embeddings = not id_exists(
        bigquery_client_helper=bigquery_client_helper,
        table_id=bigquery_client_helper.embeddings_table_id,
        id_column="isbn",
        id=add_book_request.isbn,
    )
    embeddings_payload = []
    if need_embeddings:
        # Prepare the data for the 'N' rows in the embeddings table
        # TODO:  Fetch more text besides just the user supplied ones
        embeddings_info: list[EmbeddingsGenerator.EmbeddingsInfo] = EmbeddingsGenerator.generate_embeddings(tags=add_book_request.tags, relevant_text=[add_book_request.relevant_text])
        for info in embeddings_info:

            emb_list = info.embeddings
            if hasattr(emb_list, "tolist"):
                emb_list = emb_list.tolist()
            # if it's a numpy scalar or other, coerce to list
            emb_list = list(map(float, emb_list))

            embeddings_payload.append({
                "isbn": add_book_request.isbn,
                "content": info.text,
                "embeddings": emb_list,
                "model_name": EmbeddingsGenerator.MODEL_FILE,
                "created_at": utc_now.isoformat(),   # ISO string
            })

    embeddings_json = json.dumps(embeddings_payload)

    # --- 2. Create the unified Multi-Statement SQL Script ---

    # The script uses one set of parameters for the source row, 
    # and another single ARRAY<STRUCT> parameter for all the embeddings rows.
    transaction_script = f"""
    BEGIN TRANSACTION;

    -- Insert the single source row
    INSERT INTO `{source_table_id}` (id, owner, isbn, title, author, last_read, created_at)
    VALUES (@id, @owner, @isbn, @title, @author, @last_read, @created_at);

    -- Insert embeddings parsed from JSON array parameter
    INSERT INTO `{embeddings_table_id}` (isbn, content, embeddings, model_name, created_at)
    SELECT
      JSON_VALUE(elem, '$.isbn') AS isbn,
      JSON_VALUE(elem, '$.content') AS content,
      (
        SELECT ARRAY_AGG(CAST(JSON_VALUE(e, '$') AS FLOAT64))
        FROM UNNEST(JSON_EXTRACT_ARRAY(elem, '$.embeddings')) AS e
      ) AS embeddings,
      JSON_VALUE(elem, '$.model_name') AS model_name,
      CAST(JSON_VALUE(elem, '$.created_at') AS TIMESTAMP) AS created_at
    FROM UNNEST(JSON_EXTRACT_ARRAY(@embeddings_json)) AS elem;

    COMMIT TRANSACTION;
    """

    # --- 3. Map all data to QueryJobConfig Parameters ---
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            # Parameters for the source table (Scalar types)
            bigquery.ScalarQueryParameter("id", "STRING", id),
            bigquery.ScalarQueryParameter("owner", "STRING", add_book_request.owner),
            bigquery.ScalarQueryParameter("isbn", "STRING", add_book_request.isbn),
            bigquery.ScalarQueryParameter("title", "STRING", add_book_request.title),
            bigquery.ScalarQueryParameter("author", "STRING", add_book_request.author),
            bigquery.ScalarQueryParameter("last_read", "TIMESTAMP", None),
            bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", utc_now),
            bigquery.ScalarQueryParameter("embeddings_json", "STRING", embeddings_json)
        ]
    )

    # --- 4. Execute the single atomic job ---
    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=job_config)
        # Waiting on the result means we wait for the COMMIT to finish
        query_job.result() 
        print(f"Full non-streaming transaction committed successfully for ISBN: {add_book_request.isbn}.")
        print(f"Inserted {len(embeddings_payload)} embedding rows.")

    except Exception as e:
        print(f"Transaction failed and was rolled back: {e}")
        # BigQuery automatically rolls back the entire transaction if an error occurs within the script
        raise # Re-raise the error for upstream handling

    return

def id_exists(bigquery_client_helper: BigQueryClientHelper, table_id:str, id_column:str, id: str) -> bool:
    table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{table_id}"
    query = f"""
        SELECT
            COUNT(*) as row_count
        FROM
            `{table_ref}`
        WHERE
            {id_column} = @id_param
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id_param", "STRING", id)
        ]
    )

    query_job = bigquery_client_helper.client.query(query, job_config=job_config)

    # We should only get a single row with one column
    row = next(query_job.result())
    row_count = row["row_count"]

    return row_count > 0

