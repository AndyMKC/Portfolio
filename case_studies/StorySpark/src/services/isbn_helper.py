import requests
from typing import List

def get_all_isbns_for_isbn(isbn: str) -> List[str]:
    """
    Given an ISBN, returns all ISBN-10 and ISBN-13 values
    for every edition of the same work on Open Library.
    """
    # 1. Fetch the edition data to discover the work key
    edition_url = f"https://openlibrary.org/isbn/{isbn}.json"
    resp = requests.get(edition_url, timeout=5.0)
    resp.raise_for_status()
    edition_data = resp.json()

    # 2. Extract the first work key
    works = edition_data.get("works", [])
    if not works:
        raise ValueError(f"No work record found for ISBN {isbn}")
    work_key = works[0]["key"]  # e.g. "/works/OL19551862W"

    # 3. Fetch all editions of that work
    editions_url = f"https://openlibrary.org{work_key}/editions.json"
    params = {"limit": 100}
    editions_resp = requests.get(editions_url, params=params, timeout=5.0)
    editions_resp.raise_for_status()
    editions = editions_resp.json().get("entries", [])

    # 4. Collect all ISBN-10 and ISBN-13 values
    isbns = set()
    for e in editions:
        for field in ("isbn_10", "isbn_13"):
            for code in e.get(field, []):
                isbns.add(code)

    return sorted(isbns)


# Example usage
if __name__ == "__main__":
    isbn_input = "9780763680077"
    all_codes = get_all_isbns_for_isbn(isbn_input)
    print(f"All ISBNs for {isbn_input}: {all_codes}")