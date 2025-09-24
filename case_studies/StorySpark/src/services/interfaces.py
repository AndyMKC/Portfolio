from typing import Protocol, Dict

class BookMetadataProvider(Protocol):
    def fetch(self, all_isbns: list) -> Dict:
        """Fetch normalized book metadata for a given ISBN."""
        ...