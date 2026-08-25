import logging
from fastapi import APIRouter, Depends
from app.models import Book, CleanedISBN
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from google.cloud import bigquery
from app.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("app-log")


@router.get("/books", response_model=list[Book], operation_id="GetAllBooks")
async def get_all_books(
    current_user: dict = Depends(get_current_user)
    ) -> list[Book]:
    """
    Retrieves all the books owned by the authenticated user.
    """
    owner = current_user["email"]
    logger.info(f"GetAllBooks called by user: {owner}")

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

    try:
        if bigquery_client_helper.client is None:
            # DEV_MODE: Return mock data for debugging
            logger.info("DEV_MODE: Returning mock book data")
            return [
                Book(
                    id="1",
                    owner=owner,
                    isbn=CleanedISBN(isbn="978-0-13-468599-2"),
                    title="Mock Book 1",
                    authors=["Mock Author"],
                    last_read="2024-01-01",
                    created_at="2024-01-01T00:00:00"
                ),
                Book(
                    id="2",
                    owner=owner,
                    isbn=CleanedISBN(isbn="978-0-596-52068-7"),
                    title="Mock Book 2",
                    authors=["Another Mock Author"],
                    last_read="2024-02-01",
                    created_at="2024-02-01T00:00:00"
                )
            ]
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
    except Exception as e:
        logger.error(f"GetAllBooks failed: {e}")
        raise
