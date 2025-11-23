from fastapi import APIRouter
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud.bigquery import TableReference
from typing import Dict, Any

from app.models import AddBookRequest, Book
from app.books.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper
from app.books.embeddings_generator import EmbeddingsGenerator

router = APIRouter()

@router.post("/books", response_model=Dict[str, Any], status_code=201, operation_id="AddBook")
async def add_book(req: AddBookRequest):
    bigquery_client_helper = get_bigquery_client()

    # TODO:  Figure out what we want to do to have error handling -- try:
    source_table_ref = bigquery_client_helper.client.dataset(bigquery_client_helper.dataset_id).table(bigquery_client_helper.source_table_id)
    embddings_table_ref = bigquery_client_helper.client.dataset(bigquery_client_helper.dataset_id).table(bigquery_client_helper.embeddings_table_id)
    # TODO:  Do I send in the source_table_ref or source_table_id?
    # INSERT INTO `my_dataset.table1` (
    if source_table_ref:
        raise Exception("figure out TODO")
    # TODO:  This may cause the same book to be considered two different entries since one can be ISBN-13 and one can be ISBN-10
    id = f"{req.owner}:{req.isbn}"
    if id_exists(bigquery_client_helper=bigquery_client_helper, table=source_table_ref, id=key):
        raise Exception(f"Book with isbn {req.isbn} already exists for owner {req.owner}")

    utc_now = datetime.now(timezone.utc).isoformat()
    embeddings = EmbeddingsGenerator.generate_embeddings([req.relevant_text])
    # TODO:  Only add to the embeddings table if it does not exist already
    # TODO:  add code to fetch title and author instead of relying on the customer to supply this information
    # TODO:  Fetch more text besides just the user supplied ones

    # Commit both changes at once
    transaction =f"""
BEGIN TRANSACTION;

INSERT INTO `{source_table_ref}` (
id,
owner,
isbn,
title,
author,
last_read,
created_at
)
VALUES (
'{id}',
'{req.owner}',
'{req.isbn}',
'{req.title}',
'{req.author}',
NULL,
TIMESTAMP('{utc_now}')
);

INSERT INTO `{embddings_table_ref}` (
isbn,
content,
embeddings,
model_name,
embeddings_created_at
)
VALUES (
'{req.isbn}',
'{req.relevant_text}',
{embeddings},  -- embeddings as array literal
'{EmbeddingsGenerator.MODEL_NAME}',
TIMESTAMP('{utc_now}')
);

COMMIT TRANSACTION;
"""
    return {
        # TODO:  Figure out what we want to return
    }

def id_exists(bigquery_client_helper: BigQueryClientHelper, table: TableReference, id: str) -> bool:
    table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    query = f"""
        SELECT
            COUNT(*) as row_count
        FROM
            `{table_ref}`
        WHERE
            id = @id_param
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