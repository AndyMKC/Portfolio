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
    GCP credentials are unavailable (the Cloud Logging handler is simply
    skipped in that case).

This eliminates the previous dual-logging mess where some endpoints used
``logging.getLogger(...)`` and others used
``request.app.state.cloud_logging_client.logger(...)`` directly.
"""

import logging
import os

from google.cloud import logging as cloud_logging


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
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(console)

    return client
