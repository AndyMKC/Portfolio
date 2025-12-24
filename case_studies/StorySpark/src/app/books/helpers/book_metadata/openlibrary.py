import requests
from .bookmetdataprovider import BookMetadataProvider

OPENLIBRARY_URL = "https://openlibrary.org"

class OpenLibraryProvider:
    def get_title_and_authors(isbn: str) -> tuple[str, list[str]]:
        resp = requests.get(
            f"{OPENLIBRARY_URL}/api/books",
            params={
                "bibkeys": f"ISBN:{isbn}",
                "format": "json",
                "jscmd": "data",
            },
            timeout=5.0,
        )
        resp.raise_for_status()
        isbn_data = resp.json().get(f"ISBN:{isbn}", {})
        title = isbn_data.get("title", "")
        authors = [author["name"] for author in isbn_data.get("authors", [])]

        return title, authors

    def fetch(self, isbns: list) -> dict[str, list[str]]:
        unique_isbns = list(set(isbns))
        
        isbn_metadata = {}
        for isbn in unique_isbns:
            # Get the OpenLibrary works key
            resp_isbn = requests.get(
                f"{OPENLIBRARY_URL}/api/books",
                params={
                    "bibkeys": ",".join(f"ISBN:{isbn}" for isbn in unique_isbns),
                    "format": "json",
                    "jscmd": "data",
                },
                timeout=5.0,
            )
            resp_isbn.raise_for_status()

            openlibrary_identifiers = (
                resp_isbn.json()
                    .get(f"ISBN:{isbn}", {})
                    .get("identifiers", {})
                    .get("openlibrary", [])
            )
            if not openlibrary_identifiers or len(openlibrary_identifiers) <= 0:
                continue
            
            relevant_strings = []
            for identifier in openlibrary_identifiers:
                resp_identifier = requests.get(
                    f"{OPENLIBRARY_URL}/books/{identifier}.json",
                    timeout=5.0,
                    )
                resp_identifier.raise_for_status()
                
                works = resp_identifier.json().get("works", [])
                if not works or len(works) <= 0:
                    continue
                for work in works:
                    work_key = work.get("key")
                    if not work_key:
                        continue;
                    
                    resp_work_key = requests.get(
                        f"{OPENLIBRARY_URL}/{work_key}.json",
                        timeout=5.0,
                    )
                    resp_work_key.raise_for_status()
                    resp_work_key_json = resp_work_key.json()
                    # Gather the relevant strings from various parts of the JSON
                    relevant_strings.extend([subj for subj in resp_work_key_json.get("subjects", [])])
                    # Description and notes are whole sentences as opposed to 1-3 words in subjects.  We will eventually need to parse it better.
                    if (value := resp_work_key_json.get("description")):
                        relevant_strings.append(value)
                    # if (value := resp_work_key_json.get("notes", {}).get("value")):
                    #     relevant_strings.append(value)
            
            isbn_metadata[isbn] = relevant_strings

        return isbn_metadata