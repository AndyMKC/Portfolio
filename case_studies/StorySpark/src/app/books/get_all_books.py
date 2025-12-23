from fastapi import APIRouter, Query
from app.models import Book
from google.cloud import bigquery
from app.books.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper

router = APIRouter()

@router.get("/books", response_model=list[Book], operation_id="GetAllBooks")
async def get_all_books(
    owner_id: str = Query(..., example="user@gmail.com")
    ) -> list[Book]:
    """
    Retrieves all the books owned by this user
    """
    bigquery_client_helper = get_bigquery_client()
    table_id = f"{bigquery_client_helper.source_table_id}"
    table_ref = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{table_id}"

    query = f"""
        SELECT
            *
        FROM
            `{table_ref}`
        WHERE
            owner = @id_param
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id_param", "STRING", owner_id)
        ]
    )

    query_job = bigquery_client_helper.client.query(query, job_config=job_config)
    rows = query_job.result()
    all_books = []
    for row in rows:
        book = Book(
            id=row['id'],
            owner=row['owner'],
            isbn=row['isbn'],
            title=row['title'],
            author=row['author'],
            last_read=row['last_read'],
            created_at=row['created_at']
        )
        all_books.append(book)

    return all_books
    # TODO:  Return all books from this specific owner
    # from datetime import datetime, timezone
    # utc_now = datetime.now(timezone.utc)
    # book = Book(
    #     id="internal_id",
    #     title="req.title",
    #     author="req.author",
    #     owner_id="req.owner_id",
    #     book_id="req.book_id",
    #     relevant_text="req.relevant_text",
    #     created_at=utc_now,
    #     updated_at=utc_now,
    # )
    # return list([book])



