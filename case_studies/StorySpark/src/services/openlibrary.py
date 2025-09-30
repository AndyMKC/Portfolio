import requests
from .interfaces import BookMetadataProvider

OPENLIBRARY_URL = "https://openlibrary.org/api/books"

class LocalOpenLibraryProvider:
    def fetch(self, all_isbns: list) -> list:
        resp = requests.get(
            OPENLIBRARY_URL,
            params={
                "bibkeys": ",".join(f"ISBN:{isbn}" for isbn in all_isbns),
                "format": "json",
                "jscmd": "details",
            },
            timeout=5.0,
        )
        resp.raise_for_status()

        relevant_strings = []
        for isbn in all_isbns:
            if not resp.json().get(f"ISBN:{isbn}"):
                continue
            data = resp.json().get(f"ISBN:{isbn}").get("details")
            if not data:
                raise ValueError("OpenLibrary: not found")
            
            # Gather the relevant strings from various parts of the JSON
            relevant_strings.extend([subj for subj in data.get("subjects", [])])
            # Description and notes are whole sentences as opposed to 1-3 words in subjects.  We will eventually need to parse it better.
            if (value := data.get("description", {}).get("value")):
                relevant_strings.append(value)
            if (value := data.get("notes", {}).get("value")):
                relevant_strings.append(value)

        processed_relevant_strings = sorted(set(relevant_strings))
        return processed_relevant_strings