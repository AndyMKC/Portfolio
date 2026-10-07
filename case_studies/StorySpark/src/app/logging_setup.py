"""
Centralized logging configuration for StorySpark.

Strategy
--------
  * Uses Python's standard ``logging`` library **exclusively**.
    Every module simply does::

        import logging
        logger = logging.getLogger("app-log")

  * ``setup_cloud_logging()`` (called once at app start-up) attaches a
    Google Cloud Logging handler to the **root** logger.  Because Python's
    logging propagates from child loggers to the root logger by default,
    every ``logging.getLogger("app-log")`` call automatically flows to
    GCP Cloud Logging — no direct use of the cloud-logging client is
    needed in any endpoint.

  * A console ``StreamHandler`` with a human-readable format is also
    attached so logs remain visible during local development even when
    GCP credentials are unavailable (the cloud-logging handler is simply
    skipped in that case).

  * ``trace_id`` and ``request_id`` are injected into every log record via
    a custom filter, populated from context variables set by the
    ``log_requests`` middleware. This allows correlating all telemetry
    for a single request in Cloud Logging.
"""

import logging
import os
from contextvars import ContextVar

from google.cloud import logging as cloud_logging

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get("-")
        record.request_id = request_id_var.get("-")
        return True


def setup_cloud_logging() -> "cloud_logging.Client | None":
    """
    Configure the root logger to send logs to Google Cloud Logging.

    Returns the Cloud Logging client, or ``None`` if Cloud Logging could
    not be initialised (e.g. when running locally without GCP
    credentials).
    """
    client = None
    try:
        client = cloud_logging.Client(
            project=os.environ.get("STORYSPARK_GCP_BQ_PROJECT_ID")
        )
        client.setup_logging()  # attaches a CloudLoggingHandler to the root logger
    except Exception:
        # Cloud Logging unavailable — fall back to stdlib logging only.
        pass

    # --- Console handler so local dev always has output -----------------
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Remove pre-existing StreamHandlers so they don't duplicate console
    # output (the cloud-logging handler and our console handler below are
    # the only ones we want).
    for handler in list(root.handlers):
        if isinstance(handler, logging.StreamHandler):
            root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] [trace=%(trace_id)s][request=%(request_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    console.addFilter(_CorrelationFilter())
    root.addHandler(console)

    # Ensure the cloud logging handler also gets the correlation filter
    # so trace/request IDs appear in Cloud Logging structured fields.
    for handler in list(root.handlers):
        if handler is not console:
            handler.addFilter(_CorrelationFilter())

    return client
