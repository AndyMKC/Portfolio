from typing import Dict, List
from .provider_factory import (
    get_openlibrary_provider,
    get_internet_archive_provider,
)
from services.isbn_helper import get_all_isbns_for_isbn

def gather_metadata(isbn: str) -> Dict[str, Dict]:
    """
    Calls each metadata provider and returns a dict keyed by source.
    E.g. {
      "openlibrary": { ... },
      "internet_archive": { ... }
    }
    """

    # Some places lack description for a certain edition of a book so we have to resolve all the possible ISBNs first
    all_isbns: List[str] = get_all_isbns_for_isbn(isbn)

    sources = {
        "internet_archive": get_internet_archive_provider(),
        "openlibrary": get_openlibrary_provider(),
    }

    results: Dict[str, Dict] = {}

    for source_name, provider in sources.items():
        try:
            data = provider.fetch(all_isbns)
            if source_name in results:
                raise ValueError(f"Duplicate source name:  {source_name}")
                #results[source_name].update(data)
            else:
                results[source_name] = data
        except Exception as ex:
            # you can choose to drop missing sources or surface errors
            results[source_name] = {"error": str(ex)}

    return results