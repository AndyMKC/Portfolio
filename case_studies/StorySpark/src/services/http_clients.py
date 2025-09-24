import os
import requests
from .interfaces import BookMetadataProvider

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:7071/api/mcp")

class RemoteOpenLibraryProvider:
    def fetch(self, isbn: str) -> dict:
        resp = requests.get(f"{MCP_BASE_URL}/openlibrary", params={"isbn": isbn})
        resp.raise_for_status()
        return resp.json()

class RemoteInternetArchiveProvider:
    def fetch(self, isbn: str) -> dict:
        resp = requests.get(f"{MCP_BASE_URL}/internetarchive", params={"isbn": isbn})
        resp.raise_for_status()
        return resp.json()