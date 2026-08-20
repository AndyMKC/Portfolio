"""
Authentication helpers for StorySpark.

All endpoint modules import ``get_current_user`` from here rather than from
``app.main`` to avoid a circular import (``main.py`` imports the routers,
which import this module for the dependency).

The Google ID token is verified with ``google.oauth2.id_token.verify_oauth2_token``
and the resulting email is checked against ``ALLOWED_USERS``.  Only the two
permitted Google accounts may call any API.

Logging is done exclusively through Python's standard ``logging`` library.
The ``app-log`` logger is wired to Google Cloud Logging at start-up by
``app.logging_setup.setup_cloud_logging()`` (which attaches a handler to the
root logger), so every ``logging.getLogger("app-log")`` call here and in the
endpoint modules automatically flows to GCP — no direct use of the
cloud-logging client is needed.
"""

import logging

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

# The only Google accounts allowed to call the APIs.
ALLOWED_USERS = [
    "andy.ming.kong.cheng@gmail.com",
    "codingdolly@gmail.com",
]


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Validates Google ID token and returns user information."""

    # Production mode: require Google ID token
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
    # even if the user is later denied (403).
    request.state.current_user_email = user_email

    if user_email not in ALLOWED_USERS:
        logger.warning(f"Unauthorized access attempt by: {user_email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized",
        )

    logger.info(f"Authenticated user: {user_email}")
    return {"email": user_email, "idinfo": idinfo}
