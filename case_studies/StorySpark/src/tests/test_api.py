"""
End-to-end API tests for StorySpark.

Covers:
  * Authentication (401 — no token, 401 — invalid token, 200 — authenticated user)
  * All 7 book endpoints with mocked BigQuery
  * The /healthz public endpoint
  * Structured logging (extra fields on log records)
"""
import logging
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limiter import (
    get_rate_limiter,
    init_rate_limiter,
    RateLimitConfig,
)


# --- Fixtures ----------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app=app, raise_server_exceptions=False)


@pytest.fixture
def fake_idinfo_allowed():
    return {"email": "spoofed@gmail.com", "sub": "1"}


@pytest.fixture
def mock_bq_helper():
    """Returns a mock BigQueryClientHelper with a mock client whose
    query() returns a mock job whose result() returns an empty list."""
    helper = MagicMock()
    helper.project_id = "test-project"
    helper.dataset_id = "test_dataset"
    helper.source_table_id = "source_table"
    helper.embeddings_table_id = "embeddings_table"
    helper.to_dict.return_value = {"project_id": "test-project"}
    mock_job = MagicMock()
    mock_job.result.return_value = []
    helper.client.query.return_value = mock_job
    return helper


@pytest.fixture
def mock_bq_patcher(mock_bq_helper):
    """Patch get_bigquery_client in every book module that imports it."""
    modules = [
        "app.books.add_book.get_bigquery_client",
        "app.books.get_all_books.get_bigquery_client",
        "app.books.get_recommendation.get_bigquery_client",
        "app.books.remove_book.get_bigquery_client",
        "app.books.mark_read.get_bigquery_client",
        "app.books.clear_database.get_bigquery_client",
    ]
    patches = [patch(m, return_value=mock_bq_helper) for m in modules]
    for p in patches:
        p.start()
    yield mock_bq_helper
    for p in patches:
        p.stop()


@pytest.fixture
def mock_embeddings():
    """Mock EmbeddingsGenerator.generate_embeddings to return a simple object."""
    emb = MagicMock()
    emb.text = "test content"
    emb.embedding_normalized = [0.1, 0.2, 0.3]
    emb.embedding_raw = [0.1, 0.2, 0.3]
    emb.token_len = 10
    mock_cls = MagicMock()
    mock_cls.to_dict.return_value = {"model": "test.onnx"}
    mock_cls.MODEL_FILE = "test.onnx"
    mock_cls.MODEL_PATH = "test.onnx"
    mock_cls.MODEL_EXPORT_BUCKET_NAME = "test_bucket"
    mock_cls.MODEL_IMAGE_MODEL_DIR = "models"
    mock_cls.IMAGE_MODEL_DIR = "models"
    mock_cls._model_max_length = 512
    mock_cls.generate_embeddings.return_value = [emb]
    with patch("app.books.add_book.EmbeddingsGenerator", mock_cls), \
         patch("app.books.get_recommendation.EmbeddingsGenerator", mock_cls):
        yield mock_cls


@pytest.fixture
def mock_metadata_helpers():
    """Mock id_exists, get_providers, and OpenLibraryProvider in add_book."""
    with patch("app.books.add_book.id_exists", return_value=False), \
         patch("app.books.add_book.get_providers", return_value=[]), \
         patch("app.books.add_book.OpenLibraryProvider.get_title_and_authors",
               return_value=("Test Title", ["Test Author"])):
        yield


@pytest.fixture
def log_capture():
    """Capture app-log records for verifying structured logging."""
    records = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = CaptureHandler()
    handler.setLevel(logging.DEBUG)
    logger = logging.getLogger("app-log")
    logger.addHandler(handler)
    yield records
    logger.removeHandler(handler)


# --- Rate-limiting fixtures ---------------------------------------------

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the rate limiter before and after each test for isolation."""
    limiter = get_rate_limiter()
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def low_rate_limit():
    """Set a low rate limit (3 requests) for testing rate-limit behavior."""
    limiter = init_rate_limiter(
        RateLimitConfig(
            limit=3,
            window_seconds=3600,
            exempt_paths={"/healthz"},
        )
    )
    app.state.rate_limiter = limiter
    yield limiter
    # Restore default config
    init_rate_limiter(RateLimitConfig.from_env())
    app.state.rate_limiter = get_rate_limiter()
    get_rate_limiter().reset()


# --- Auth tests ---------------------------------------------------------

class TestAuth:
    """Verify authentication is enforced on all endpoints."""

    def test_healthz_no_auth(self, client):
        """/healthz should be accessible without authentication."""
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_no_token_returns_401(self, client):
        r = client.get("/books")
        assert r.status_code == 401

    def test_no_token_returns_401_post(self, client):
        r = client.post("/books", json={"owner": "spoofed@gmail.com", "isbns": []})
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client):
        with patch("app.auth.id_token.verify_oauth2_token",
                   side_effect=ValueError("invalid")):
            r = client.get("/books", headers={"Authorization": "Bearer bad-token"})
        assert r.status_code == 401

    def test_allowed_user_passes_auth(self, client, fake_idinfo_allowed, mock_bq_patcher):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.get("/books", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200


# --- Endpoint tests (with auth + mocked BigQuery) ----------------------

class TestGetAllBooks:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.get("/books", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200
        assert r.json() == []

class TestAddBook:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher,
                          mock_embeddings, mock_metadata_helpers):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.post("/books", headers={"Authorization": "Bearer fake"},
                            json={"owner": "spoofed@gmail.com",
                                  "isbns": [{"isbn": "978-0448487311"}]})
        assert r.status_code == 201

    def test_payload_logging(self, client, fake_idinfo_allowed, mock_bq_patcher,
                             mock_embeddings, mock_metadata_helpers, log_capture):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            client.post("/books", headers={"Authorization": "Bearer fake"},
                        json={"owner": "spoofed@gmail.com",
                              "isbns": [{"isbn": "978-0448487311"}]})

        # Find the AddBook log record and verify extra fields
        for rec in log_capture:
            if "AddBook called by user" in rec.getMessage():
                assert getattr(rec, "user_email", None) == "spoofed@gmail.com"
                assert getattr(rec, "add_book_request", None) is not None
                assert "isbns" in getattr(rec, "add_book_request", {})
                return
        pytest.fail("AddBook log record with payload not found")


class TestGetRecommendation:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher, mock_embeddings):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.get("/books/recommendation?text=canoe&limit=5",
                           headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

class TestRemoveBook:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.delete("/books/978-0448487311",
                              headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

class TestMarkRead:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.patch("/books/978-0448487311/mark_read",
                             headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

class TestClearDatabase:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.delete("/books", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

class TestClearAndSeedDb:
    def test_allowed_user(self, client, fake_idinfo_allowed, mock_bq_patcher,
                          mock_embeddings, mock_metadata_helpers, log_capture):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.post("/reset", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

    def test_passes_current_user_to_internal_calls(self, client, fake_idinfo_allowed,
                                                    mock_bq_patcher, mock_embeddings,
                                                    mock_metadata_helpers, log_capture):
        """Verify that clear_and_seed_db passes current_user to clear_database
        and add_book (i.e., no 'missing argument' crash)."""
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.post("/reset", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

        # Verify log chain: ClearAndSeedDb -> ClearDatabase -> AddBook
        messages = [rec.getMessage() for rec in log_capture]
        assert any("ClearAndSeedDb called by user" in m for m in messages)
        assert any("ClearDatabase called by user" in m for m in messages)
        assert any("AddBook" in m for m in messages)


# --- Middleware logging ------------------------------------------------

class TestMiddlewareLogging:
    def test_logs_who_called_what(self, client, fake_idinfo_allowed, mock_bq_patcher,
                                  mock_embeddings, mock_metadata_helpers, log_capture):
        with patch("app.auth.id_token.verify_oauth2_token", return_value=fake_idinfo_allowed):
            r = client.post("/books", headers={"Authorization": "Bearer fake"},
                            json={"owner": "spoofed", "isbns": [{"isbn": "978-0448487311"}]})
        assert r.status_code == 201

        # Middleware should log the API call with the authenticated user
        messages = [rec.getMessage() for rec in log_capture]
        assert any(
            "API call: POST /books by spoofed@gmail.com -> 201" in m
            for m in messages
        )

    def test_logs_unauthenticated_requests(self, client, log_capture):
        r = client.get("/books")
        assert r.status_code == 401
        messages = [rec.getMessage() for rec in log_capture]
        assert any(
            "API call: GET /books" in m and "unauthenticated" in m.lower()
            for m in messages
        )


# --- Rate limiting -------------------------------------------------------

class TestRateLimiting:
    """Verify rate limiting on all API endpoints."""

    def test_healthz_is_exempt(self, client, low_rate_limit):
        """/healthz should not be affected by rate limiting."""
        for i in range(10):
            r = client.get("/healthz")
            assert r.status_code == 200

    def test_docs_not_rate_limited(self, client, low_rate_limit):
        """Swagger UI and OpenAPI JSON should not be rate limited."""
        for i in range(10):
            r = client.get("/docs")
            assert r.status_code == 200
            r = client.get("/openapi.json")
            assert r.status_code == 200

    def test_requests_allowed_under_limit(self, client, low_rate_limit,
                                          fake_idinfo_allowed, mock_bq_patcher):
        """Requests within the limit (3) should succeed."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            for i in range(3):
                r = client.get("/books",
                               headers={"Authorization": "Bearer fake"})
                assert r.status_code == 200

    def test_rate_limit_returns_429(self, client, low_rate_limit,
                                    fake_idinfo_allowed, mock_bq_patcher):
        """The 4th request should return 429 Too Many Requests."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            # First 3 requests are allowed
            for i in range(3):
                r = client.get("/books",
                               headers={"Authorization": "Bearer fake"})
                assert r.status_code == 200
            # 4th request should be rate limited
            r = client.get("/books",
                           headers={"Authorization": "Bearer fake"})
            assert r.status_code == 429
            assert "Retry-After" in r.headers

    def test_rate_limit_headers_on_success(self, client, low_rate_limit,
                                           fake_idinfo_allowed, mock_bq_patcher):
        """Successful responses should include rate-limit headers."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            r = client.get("/books",
                           headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200
        assert r.headers["X-RateLimit-Limit"] == "3"
        assert r.headers["X-RateLimit-Remaining"] == "2"

    def test_rate_limit_headers_on_429(self, client, low_rate_limit,
                                       fake_idinfo_allowed, mock_bq_patcher):
        """429 responses should include rate-limit headers."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            for i in range(3):
                client.get("/books",
                           headers={"Authorization": "Bearer fake"})
            r = client.get("/books",
                           headers={"Authorization": "Bearer fake"})
        assert r.status_code == 429
        assert r.headers["X-RateLimit-Limit"] == "3"
        assert r.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in r.headers

    def test_rate_limit_429_response_body(self, client, low_rate_limit,
                                         fake_idinfo_allowed, mock_bq_patcher):
        """429 response body should include retry_after_seconds."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            for i in range(3):
                client.get("/books",
                           headers={"Authorization": "Bearer fake"})
            r = client.get("/books",
                           headers={"Authorization": "Bearer fake"})
        assert r.status_code == 429
        data = r.json()
        assert "detail" in data
        assert "Rate limit exceeded" in data["detail"]
        assert "retry_after_seconds" in data
        assert data["retry_after_seconds"] > 0

    def test_per_client_rate_limits(self, client, low_rate_limit,
                                    fake_idinfo_allowed, mock_bq_patcher):
        """Different clients (by IP) have separate rate limit buckets."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            # Exhaust limit for client 1 (default IP, no X-Forwarded-For)
            for i in range(3):
                r = client.get("/books",
                               headers={"Authorization": "Bearer fake"})
                assert r.status_code == 200
            # Client 1 is now rate limited
            r = client.get("/books",
                           headers={"Authorization": "Bearer fake"})
            assert r.status_code == 429
            # Client 2 (different IP via X-Forwarded-For) still allowed
            r = client.get(
                "/books",
                headers={"Authorization": "Bearer fake",
                         "X-Forwarded-For": "10.0.0.2"},
            )
            assert r.status_code == 200

    def test_rate_limit_applies_to_all_endpoints(self, client, low_rate_limit,
                                                  fake_idinfo_allowed,
                                                  mock_bq_patcher, mock_embeddings,
                                                  mock_metadata_helpers):
        """Rate limiting applies to POST endpoints too (e.g. /books)."""
        with patch("app.auth.id_token.verify_oauth2_token",
                   return_value=fake_idinfo_allowed):
            for i in range(3):
                r = client.post(
                    "/books",
                    headers={"Authorization": "Bearer fake"},
                    json={"owner": "spoofed",
                          "isbns": [{"isbn": "978-0448487311"}]},
                )
                assert r.status_code == 201
            # 4th request should be rate limited
            r = client.post(
                "/books",
                headers={"Authorization": "Bearer fake"},
                json={"owner": "spoofed",
                      "isbns": [{"isbn": "978-0448487311"}]},
            )
            assert r.status_code == 429
