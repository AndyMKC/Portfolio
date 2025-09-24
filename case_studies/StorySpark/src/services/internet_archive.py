import requests
from .interfaces import BookMetadataProvider

IA_API_URL = "https://archive.org/metadata"

class LocalInternetArchiveProvider:
    def fetch(self, all_isbns: list) -> list:
        # Given each ISBN, fetch the "work" it is associated with.  Different editions of the same book should share the same work.
        metadata = list()

        editions_filtered = LocalInternetArchiveProvider.get_editions(all_isbns)
        # Now that we have the work (there should be only one but we will iterate through as a precaution)
        for edition in editions_filtered:
            metadata_for_edition = LocalInternetArchiveProvider.get_metadata_for_edition(edition)
            metadata.extend(metadata_for_edition)

        return sorted(set(metadata))
    
    def get_editions(all_isbns:list) -> list:
        query = " OR ".join(f"isbn:{isbn}" for isbn in all_isbns)
        params = {
            "q": f"({query})",
            "fl[]": "identifier",
            "rows": 100,
            "output": "json",
        }

        resp = requests.get(
            "https://archive.org/advancedsearch.php",
            params=params,
            timeout=5.0,
        )
        resp.raise_for_status()

        data = resp.json()
        editions = (x.get("identifier") for x in data.get("response", {}).get("docs", []) if x.get("identifier"))
        # Some entries in internet archive are stuff that comes in some bundles or free deliveries.  For example, https://archive.org/advancedsearch.php?q=isbn:0763680079%20OR%20isbn:0857633872%20OR%20isbn:0857633880%20OR%20isbn:8416363544%20OR%20isbn:9780763680077%20OR%20isbn:9780857633873%20OR%20isbn:9780857633880%20OR%20isbn:9788416363544&fl[]=identifier&rows=100&output=json will return things such as "bwb_daily_pallets_2021-06-10", "bwb_daily_pallets_2021-06-16", "BWB-2020-01-30", and ""books_neverscan_session_009" which are not the ones we are looking for.  The one we are looking for is "princessgiant0000hart".  We need to do some elementary filtering.  We cannot rely on the presence of "_" since there have been times the underscore does appear.
        editions_filtered = [e for e in editions if not e.lower().startswith("bwb_") and not e.lower().startswith("books_") and not e.lower().startswith("bwb-")]

        return editions_filtered

    def get_metadata_for_edition(edition: str) -> list:
        resp = requests.get(
            f"https://archive.org/metadata/{edition}",
            params=None,
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json().get("metadata", {})

        relevant_strings = []
        # Gather the relevant strings from various parts of the JSON
        relevant_strings.extend([subj for subj in data.get("subject", [])])
        # Description and title are whole sentences as opposed to 1-3 words in subjects.  We will eventually need to parse it better.
        relevant_strings.extend([desc for desc in data.get("description", [])]) 
        if (value := data.get("title", {})):
            relevant_strings.append(value)

        return relevant_strings
        