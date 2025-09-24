import requests
from .interfaces import BookMetadataProvider

IA_API_URL = "https://archive.org/metadata"

class LocalInternetArchiveProvider:
    def fetch(self, all_isbns: list) -> dict:
        # 1. Given the ISBN, fetch all the relevant edition data to find the work key
        editions = []

        for isbn in all_isbns:
            edition_url = f"https://openlibrary.org/isbn/{isbn}.json"
            resp = requests.get(edition_url, timeout=5.0)
            resp.raise_for_status()
            edition_data = resp.json()

        