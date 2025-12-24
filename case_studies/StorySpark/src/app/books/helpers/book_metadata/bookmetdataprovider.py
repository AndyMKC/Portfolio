from typing import Protocol

class BookMetadataProvider(Protocol):
    def fetch(self, isbns: list) -> dict[str, list[str]]:
        """Fetch normalized book metadata for a given ISBN."""
        ...