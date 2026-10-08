"""
Authentication helpers for StorySpark.

All endpoint modules import ``get_current_user`` from here rather than from
``app.main`` to avoid a circular import (``main.py`` imports the routers,
which import this module for the dependency).

The Google ID token is verified with ``google.oauth2.id_token.verify_oauth2_token``.
Supports both Bearer tokens (manual/API clients) and IAP JWT assertions
(injected by Identity-Aware Proxy for browser users).

Logging is done exclusively through Python's standard ``logging`` library.
The ``app-log`` logger is wired to Google Cloud Logging at start-up by
``app.logging_setup.setup_cloud_logging()`` (which attaches a handler to the
root logger), so every ``logging.getLogger("app-log")`` call here and in the
endpoint modules automatically flows to GCP — no direct use of the
cloud-logging client is needed.
"""

import logging
import os

from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Module-level logger — flows to GCP Cloud Logging via setup_cloud_logging().
logger = logging.getLogger("app-log")

# HTTP Bearer scheme — clients send a Google ID token as a Bearer token.
# FastAPI automatically adds a ``bearerAuth`` security scheme to the OpenAPI
# document for every endpoint that uses ``Depends(get_current_user)``,
# which makes Swagger UI show lock icons on protected routes and an
# "Authorize" button for pasting the token.
bearer_scheme = HTTPBearer()

# IAP audience format: /projects/{project_number}/global/backendServices/{service_id}
# Set via environment variable in Cloud Run
IAP_AUDIENCE = os.environ.get("IAP_AUDIENCE")


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Validates Google ID token (Bearer or IAP) and returns user information."""

    # 1. Try IAP header first (for browser users via IAP)
    iap_jwt = request.headers.get("X-Goog-IAP-JWT-Assertion")
    if iap_jwt:
        if not IAP_AUDIENCE:
            logger.error("IAP_AUDIENCE not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication configuration error",
            )
        try:
            idinfo = id_token.verify_oauth2_token(
                iap_jwt,
                requests.Request(),
                audience=IAP_AUDIENCE,
                clock_skew_in_seconds=10,
            )
            user_email = idinfo.get("email")
            if user_email:
                request.state.current_user_email = user_email
                logger.info(f"Authenticated user via IAP: {user_email}")
                return {"email": user_email, "idinfo": idinfo}
        except ValueError as e:
            logger.warning(f"IAP JWT verification failed: {e}")
            # Fall through to Bearer token validation

    # 2. Fallback: Bearer token (for Swagger manual paste, API clients)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            clock_skew_in_seconds=10,
        )
    except ValueError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_email = idinfo.get("email")
    if not user_email:
        logger.warning("Token verification failed: no email claim found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Store on request.state so the middleware can log "who called what"
    request.state.current_user_email = user_email

    logger.info(f"Authenticated user: {user_email}")
    return {"email": user_email, "idinfo": idinfo}
