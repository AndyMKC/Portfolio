from fastapi import APIRouter
from datetime import datetime, timezone
from google.cloud import bigquery
from typing import Dict, Any

from app.models import AddBookRequest, Book
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

    # TODO:  add code to fetch title and author instead of relying on the customer to supply this information
    # TODO:  Fetch more text besides just the user supplied ones
    # We want to not have any issues where there is an entry in the source table and not something in the embeddings table so commit both changes at once
    transaction = f"""
BEGIN TRANSACTION;

INSERT INTO `{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}` (
id,
owner,
isbn,
title,
author,
last_read,
created_at
)
VALUES (
@source_id,
@source_owner,
@source_isbn,
@source_title,
@source_author,
NULL,
@source_created_at
);
"""
    if False == id_exists(bigquery_client_helper=bigquery_client_helper, table_id=bigquery_client_helper.embeddings_table_id, id_column="isbn", id=req.isbn):
        embeddings = EmbeddingsGenerator.generate_embeddings([req.relevant_text])
        transaction += f"""

INSERT INTO `{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}` (
isbn,
content,
embeddings,
model_name,
embeddings_created_at
)
VALUES (
@embeddings_isbn,
@embeddings_content,
@embeddings_embeddings,
@embeddings_model_name,
@embeddings_created_at
);
        """

    transaction += "COMMIT TRANSACTION;"

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("source_id", "STRING", id),
            bigquery.ScalarQueryParameter("source_owner", "STRING", req.owner),
            bigquery.ScalarQueryParameter("source_isbn", "STRING", req.isbn),
            bigquery.ScalarQueryParameter("source_title", "STRING", req.title),
            bigquery.ScalarQueryParameter("source_author", "STRING", req.author),
            bigquery.ScalarQueryParameter("source_created_at", "TIMESTAMP", utc_now),

            bigquery.ScalarQueryParameter("embeddings_isbn", "STRING", req.isbn),
            bigquery.ArrayQueryParameter("embeddings_content", "STRING", [req.relevant_text]),
            bigquery.ArrayQueryParameter("embeddings_embeddings", "FLOAT64", embeddings),
            bigquery.ScalarQueryParameter("embeddings_model_name", "STRING", EmbeddingsGenerator.MODEL_NAME),
            # TODO:  change embeddings_created_a
            bigquery.ScalarQueryParameter("embeddings_created_at", "TIMESTAMP", utc_now)
        ]
    )

    job = bigquery_client_helper.client.query(query=transaction, job_config=job_config)
    job.result() # Wait for the job to complete

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