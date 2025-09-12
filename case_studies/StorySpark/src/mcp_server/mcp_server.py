# from fastapi import FastAPI
# import os

# # Create the FastAPI app instance
# app = FastAPI(
#     title="Book Info Retriever MCP Server",
#     version="1.0.0",
#     description="An MCP server that fetches information about books"
# )

# # This is an example of a simple tool for your AI agent
# # It takes a name as a parameter and returns a greeting.
# @app.get("/hello/{name}")
# async def hello(name: str):
#     """
#     Greets a person by their name.
#     """
#     return {"message": f"Hello, {name}!"}

# This is a tool for your AI agent that
# It takes the 13-digit ISBN and return

import requests
from urllib.parse import urlparse
from typing import Optional

def fetch_description_by_isbn(isbn: str, timeout: float = 10.0) -> Optional[str]:
    """
    Given a 13-digit ISBN, return the book's description from Open Library.
    Returns None if no description is found.
    """
    lookup = f"ISBN:{isbn}"
    # 1. Initial call to get info_url (which contains the OLID)
    params = {"bibkeys": lookup, "format": "json"}
    resp = requests.get("https://openlibrary.org/api/books", params=params, timeout=timeout)
    resp.raise_for_status()
    book_data = resp.json().get(lookup)
    if not book_data:
        return None

    # Extract OLID from info_url or fallback to 'url'
    info_url = book_data.get("info_url")# or book_data.get("url")
    if not info_url:
        return None
    path_parts = urlparse(info_url).path.split("/")
    if len(path_parts) < 3:
        return None
    olid = path_parts[2]

    # 2. Fetch edition JSON and try to read its description
    ed_resp = requests.get(f"https://openlibrary.org/books/{olid}.json", timeout=timeout)
    ed_resp.raise_for_status()
    ed_data = ed_resp.json()
    desc = ed_data.get("description")
    if isinstance(desc, dict):
        return desc.get("value")
    if isinstance(desc, str):
        return desc

    # 3. Fallback: fetch the work record if edition has no description
    works = ed_data.get("works", [])
    if works:
        work_key = works[0].get("key")
        if work_key:
            wk_resp = requests.get(f"https://openlibrary.org{work_key}.json", timeout=timeout)
            wk_resp.raise_for_status()
            wk_data = wk_resp.json()
            wdesc = wk_data.get("description")
            if isinstance(wdesc, dict):
                return wdesc.get("value")
            if isinstance(wdesc, str):
                return wdesc

    return None

isbn = "978-1423133094"
print(fetch_description_by_isbn(isbn))
