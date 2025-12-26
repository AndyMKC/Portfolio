from fastapi import APIRouter, Query
from app.models import Book
from google.cloud import bigquery
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from app.models import CleanedISBN

router = APIRouter()

@router.get("/books", response_model=list[Book], operation_id="GetAllBooks")
async def get_all_books(
    owner: str = Query(..., example="user@gmail.com")
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
            owner = @owner
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("owner", "STRING", owner)
        ]
    )

    query_job = bigquery_client_helper.client.query(query, job_config=job_config)
    rows = query_job.result()
    all_books = []
    for row in rows:
        book = Book(
            id=row['id'],
            owner=row['owner'],
            isbn=CleanedISBN(isbn=row['isbn']),
            title=row['title'],
            authors=row['authors'],
            last_read=row['last_read'],
            created_at=row['created_at']
        )
        all_books.append(book)

    return all_books




