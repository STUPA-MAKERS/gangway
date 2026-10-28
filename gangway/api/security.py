"""API key check for all routes."""

import os
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
"""The request header that holds the API key."""

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(
    api_key_from_header: Annotated[str | None, Security(api_key_header)],
) -> str:
    """Check the API key of a request.

    The function reads the ``API_KEY`` environment variable for each request.

    Args:
        api_key_from_header: The API key from the request header.

    Returns:
        The valid API key.

    Raises:
        HTTPException: 500 if the server has no API key, 403 if the key in
            the request is missing or wrong.
    """
    server_api_key = os.getenv("API_KEY")
    if not server_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key not configured on the server.",
        )

    if api_key_from_header == server_api_key:
        return server_api_key
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key")
