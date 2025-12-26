from fastapi import APIRouter, Request
from datetime import datetime, timezone
from google.cloud import bigquery
import json

from app.models import AddBookRequest
from app.books.helpers.bigquery_client_helper import get_bigquery_client, BigQueryClientHelper
from app.books.helpers.embeddings_generator import EmbeddingsGenerator
from app.books.helpers.book_metadata.openlibrary import OpenLibraryProvider
from app.books.helpers.book_metadata.provider_factory import get_providers

router = APIRouter()

def create_source_table_id(owner: str, isbn: str) -> str:
    return f"{owner}:{isbn}"

@router.post("/books", response_model=None, status_code=201, operation_id="AddBook")
async def add_book(
    request: Request,
    add_book_request: AddBookRequest
    ):
    """
    Inserts data into both tables atomically within a single BigQuery transaction.
    """
    bigquery_client_helper = get_bigquery_client()

    log_payload = {
        "add_book_request" : add_book_request.dict(),
        "bigquery_client_helper": bigquery_client_helper.to_dict(),
        "embeddings_generator": EmbeddingsGenerator.to_dict()
    }
    cloud_logger = request.app.state.cloud_logging_client.logger("app-log")
    cloud_logger.log_struct(log_payload, severity="INFO")

    # Uniquify the list of incoming ISBNs and only process the ones that have not been processed before
    # TODO:  This does not factor in any user-provided relevant text/tags and does not account for new providers needed to process
    unique_isbns = [isbn for isbn in list(set(add_book_request.isbns)) if not id_exists(
        bigquery_client_helper=bigquery_client_helper,
        table_id=bigquery_client_helper.source_table_id,
        id_column="id",
        id=f"{add_book_request.owner}:{isbn}"
    )]
    # Get all the metadata for each of the given ISBNs
    providers = get_providers()
    final_metadatas: dict[str, list] = { isbn: [] for isbn in unique_isbns }
    for provider in providers:
        metadatas = provider.fetch(unique_isbns)
        for isbn, metadata in metadatas.items():
            final_metadatas[isbn].extend(metadata)

    utc_now = datetime.now(timezone.utc)
    source_table_id = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    embeddings_table_id = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}"

    # Construct the objects needed to add to the source table
    source_table_data = []
    for isbn, metadata in final_metadatas.items():
        # TODO:  Not every book has a title and author (978-1-78557-934-9 "10 Little Snowmen".  Figure out some strategy to handle this.  That one coincidentally has no embeddings generatable)
        title, authors = OpenLibraryProvider.get_title_and_authors(isbn)
        source_table_data.append({
            "id": f"{add_book_request.owner}:{isbn}",
            "owner": add_book_request.owner,
            "isbn": isbn,
            "title": title,
            "authors": authors,
            "last_read": None,
            "created_at": utc_now.isoformat()
        })
    
    # Construct the objects needed to add to the embeddings table, if needed
    embeddings_table_data = []
    for isbn, metadata in final_metadatas.items():
        need_embeddings = not id_exists(
            bigquery_client_helper=bigquery_client_helper,
            table_id=bigquery_client_helper.embeddings_table_id,
            id_column="isbn",
            id=isbn,
        )
        if not need_embeddings:
            continue
        
        # TODO:  Bring back user-provided tags
        # TODO:  Should we put the title of the book as well?
        embeddings_info: list[EmbeddingsGenerator.EmbeddingsInfo] = EmbeddingsGenerator.generate_embeddings(tags="", relevant_text=metadata)
        for info in embeddings_info:
            emb_raw_list = info.embedding_raw
            emb_norm_list = info.embedding_normalized
            if hasattr(emb_raw_list, "tolist"):
                emb_raw_list = emb_raw_list.tolist()
            if hasattr(emb_norm_list, "tolist"):
                emb_norm_list = emb_norm_list.tolist()
            # if it's a numpy scalar or other, coerce to list
            emb_raw_list = list(map(float, emb_raw_list))
            emb_norm_list = list(map(float, emb_norm_list))
            embeddings_table_data.append({
                "isbn": isbn,
                "content": info.text,
                "embedding_raw": emb_raw_list,
                "embedding_normalized": emb_norm_list,
                "model_name": EmbeddingsGenerator.MODEL_FILE,
                "created_at": utc_now.isoformat(),   # ISO string
                # TODO:  Fill in owner if it is a user-provided text
                "owner": None
            })

    transaction_script = f"""
    BEGIN TRANSACTION;

    -- Insert multiple source rows
    INSERT INTO `{source_table_id}` (
        id, owner, isbn, title, authors, last_read, created_at
    )
    SELECT
        JSON_VALUE(elem, '$.id') AS id,
        JSON_VALUE(elem, '$.owner') AS owner,
        JSON_VALUE(elem, '$.isbn') AS isbn,
        JSON_VALUE(elem, '$.title') AS title,

        (
        SELECT ARRAY_AGG(JSON_VALUE(a, '$'))
        FROM UNNEST(JSON_EXTRACT_ARRAY(elem, '$.authors')) AS a
        ) AS authors,

        CAST(JSON_VALUE(elem, '$.last_read') AS TIMESTAMP) AS last_read,
        CAST(JSON_VALUE(elem, '$.created_at') AS TIMESTAMP) AS created_at
    FROM UNNEST(JSON_EXTRACT_ARRAY(@source_rows_json)) AS elem;

    -- Insert multiple embedding rows (each may have different ISBNs)
    INSERT INTO `{embeddings_table_id}` (
        isbn, content, embedding_raw, embedding_normalized, model_name, created_at, owner
    )
    SELECT
        JSON_VALUE(elem, '$.isbn') AS isbn,
        JSON_VALUE(elem, '$.content') AS content,

        (
        SELECT ARRAY_AGG(CAST(JSON_VALUE(e, '$') AS FLOAT64))
        FROM UNNEST(JSON_EXTRACT_ARRAY(elem, '$.embedding_raw')) AS e
        ) AS embedding_raw,

        (
        SELECT ARRAY_AGG(CAST(JSON_VALUE(e, '$') AS FLOAT64))
        FROM UNNEST(JSON_EXTRACT_ARRAY(elem, '$.embedding_normalized')) AS e
        ) AS embedding_normalized,

        JSON_VALUE(elem, '$.model_name') AS model_name,
        CAST(JSON_VALUE(elem, '$.created_at') AS TIMESTAMP) AS created_at,
        JSON_VALUE(elem, '$.owner') AS owner
    FROM UNNEST(JSON_EXTRACT_ARRAY(@embeddings_json)) AS elem;

    COMMIT TRANSACTION;
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "source_rows_json", "STRING", json.dumps(source_table_data)
            ),
            bigquery.ScalarQueryParameter(
                "embeddings_json", "STRING", json.dumps(embeddings_table_data)
            ),
        ]
    )

    try:
        query_job = bigquery_client_helper.client.query(transaction_script, job_config=job_config)
        # Waiting on the result means we wait for the COMMIT to finish
        query_job.result()
        print(f"Full non-streaming transaction committed successfully for ISBN: {add_book_request.isbns}.")
        print(f"Inserted {len(source_table_data)} source table rows")
        print(f"Inserted {len(embeddings_table_data)} embedding rows.")

    except Exception as e:
        print(f"Transaction failed and was rolled back: {e}")
        # BigQuery automatically rolls back the entire transaction if an error occurs within the script
        raise

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

