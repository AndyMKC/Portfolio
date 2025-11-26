from fastapi import APIRouter
from datetime import datetime, timezone
from google.cloud import bigquery
from typing import Any

from app.models import AddBookRequest
from app.books.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper
from app.books.embeddings_generator import EmbeddingsGenerator

router = APIRouter()

@router.post("/books", response_model=None, status_code=201, operation_id="AddBook")
async def add_book(req: AddBookRequest):
    bigquery_client_helper = get_bigquery_client()

    # INSERT INTO `my_dataset.table1` (
    # TODO:  This may cause the same book to be considered two different entries since one can be ISBN-13 and one can be ISBN-10
    id = f"{req.owner}:{req.isbn}"
    if id_exists(bigquery_client_helper=bigquery_client_helper, table_id=bigquery_client_helper.source_table_id, id_column="id", id=id):
        raise Exception(f"Book with isbn {req.isbn} already exists for owner {req.owner}")

    utc_now = datetime.now(timezone.utc)

    # We want to not have any issues where there is an entry in the source table and not something in the embeddings table so commit both changes at once
    source_table = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    embeddings_table = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}"

    # Prepare the single source row
    source_row: dict[str, Any] = {
        "id": id,
        "owner": req.owner,
        "isbn": req.isbn,
        # TODO:  add code to fetch title and author instead of relying on the customer to supply this information
        "title": req.title,
        "author": req.author,
        "last_read": None,
        "created_at": utc_now,
    }

    # Determine whether we need to create embeddings
    need_embeddings = not id_exists(
        bigquery_client_helper=bigquery_client_helper,
        table_id=bigquery_client_helper.embeddings_table_id,
        id_column="isbn",
        id=req.isbn,
    )

    embeddings_rows: list[dict[str, Any]] = []
    if need_embeddings:
        # Generate embeddings (returns list[list[float]])
        # TODO:  Fetch more text besides just the user supplied ones
        embeddings = EmbeddingsGenerator.generate_embeddings(tags=req.tags, relevant_text=[req.relevant_text])

        # Build one row per embedding vector
        for idx, emb in enumerate(embeddings):
            embeddings_rows.append({
                "isbn": req.isbn,
                "content": req.relevant_text or "",          # store the source content or empty string
                "embeddings": emb,                           # ARRAY<FLOAT64> column in BigQuery
                "model_name": EmbeddingsGenerator.MODEL_FILE,
                "embeddings_created_at": utc_now,
                "chunk_index": idx,                          # optional: index to identify which vector
            })

    # Transactional function
    def transaction_fn(transaction):
        # Insert the single source row
        errors_source = transaction.insert_rows_json(source_table, [source_row])
        if errors_source:
            raise RuntimeError(f"Failed to insert into {source_table}: {errors_source}")

        # Insert embedding rows (one per vector) if any
        if embeddings_rows:
            errors_embeddings = transaction.insert_rows_json(embeddings_table, embeddings_rows)
            if errors_embeddings:
                raise RuntimeError(f"Failed to insert into {embeddings_table}: {errors_embeddings}")
        
        # If no exception, transaction will be committed by run_in_transaction

        # Run transaction (will retry on transient errors)
        bigquery_client_helper.client.run_in_transaction(transaction_fn)

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

def retrieve_relevant_text(isbn: str) -> str:
    return f"Relevant text for book with ISBN {isbn}."