from fastapi import APIRouter, Query
from app.models import RecommendedBook
from app.books.helpers.bigquery_client_helper import get_bigquery_client
from app.books.helpers.embeddings_generator import EmbeddingsGenerator
from google.cloud import bigquery

router = APIRouter()

@router.get("/books/recommendation", response_model=list[RecommendedBook], operation_id="GetBookRecommendation")
async def get_recommendation(
    owner: str = Query(..., example="user@gmail.com"),
    text: str = Query(..., example="canoe")
    ) -> list[RecommendedBook]:
    embedding_info = EmbeddingsGenerator.generate_embeddings(tags=None, relevant_text=[text])[0]

    bigquery_client_helper = get_bigquery_client()
    source_table_id = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.source_table_id}"
    embeddings_table_id = f"{bigquery_client_helper.project_id}.{bigquery_client_helper.dataset_id}.{bigquery_client_helper.embeddings_table_id}"

    top_k = 10
    # TODO:  Figure out the owner stuff
    query = f"""
    DECLARE owner_param STRING DEFAULT @owner;
    DECLARE query_embedding ARRAY<FLOAT64> DEFAULT @query_embedding;

    -- Filter to only books owned by this person
    WITH owner_books AS (
        SELECT *
        FROM `{source_table_id}`
        WHERE owner = owner_param
    ),
    owner_isbns AS (
      SELECT DISTINCT isbn AS isbn
      FROM owner_books
    ),
    -- Calculate similarity scores
    scored AS (
        SELECT
            isbn,
            content,
            (
                SELECT SUM(a * b)
                FROM UNNEST(embedding_normalized) AS left WITH OFFSET row_pos
                JOIN UNNEST(query_embedding) AS right WITH OFFSET query_pos
                ON row_pos = query_pos
            ) AS cosine_similarity
        FROM `{embeddings_table_id}` as s
        WHERE s.isbn IN (SELECT isbn FROM owner_isbns)
    ),
    -- Pick the closest similarity score per ISBN
    ranked AS (
        SELECT
            isbn,
            content,
            cosine_similarity
            ROW_NUMBER() OVER
            (
                PARTITION by isbn
                ORDER BY cosine_similarity DESC
            ) AS row_num
    )
    -- Pick the best one
    best_per_isbn AS (
        SELECT
            isbn,
            content,
            cosine_sim AS best_cosine_similarity
        FROM ranked
        WHERE row_num = 1
--        ORDER BY best_cosine_similarity DESC
--        LIMIT @top_k;
    )
    -- Join back with the original table to get more information
    SELECT
        ANY_VALUE(source_table.id),
        ANY_VALUE(source_table.owner),
        best_per_isbn.isbn,
        ANY_VALUE(source_table.title),
        ANY_VALUE(source_table.authors),
        best_per_isbn.content AS relevant_text,
        ANY_VALUE(source_table.last_read),
        ANY_VALUE(source_table.created_at),
        best_per_isbn.best_cosine_similarity,
    FROM best_per_isbn
    LEFT JOIN owner_source
        ON owner_source.isbn = best_per_isbn.isbn
    GROUP BY best_per_isbn.isbn, best_per_isbn.content, best_per_isbn.best_cosine_similarity
    ORDER BY best_cosine_similarity DESC
    LIMIT @top_k
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "owner", "STRING", owner
            ),
            bigquery.ArrayQueryParameter(
                "query_embedding", "FLOAT64", embedding_info.embedding_normalized
            ),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k)
        ]
    )

    try:
        query_job = bigquery_client_helper.client.query(query=query, job_config=job_config)
        rows = query_job.result()
        all_books = []
        for row in rows:
            book = RecommendedBook(
                id=row['id'],
                owner=row['owner'],
                isbn=row['isbn'],
                title=row['title'],
                authors=row['authors'],
                relevant_text=row['relevant_text'],
                last_read=row['last_read'],
                created_at=row['created_at'],
                cosine_simularity=row['best_cosine_similarity']
            )
            all_books.append(book)
            
            return all_books
    except Exception as e:
        print(f"Query failed:  {e}")
        raise

