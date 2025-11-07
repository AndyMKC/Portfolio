import requests
from typing import Optional, Dict, Any, List
from external_info import ExternalInfo

class MailerLiteClient:
    @staticmethod
    def generate_headers(external_info: ExternalInfo) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {external_info.mailerlite_api_token}"
        }

        return headers
    
    @staticmethod
    def get_subscriber_count(external_info: ExternalInfo) -> int:
        full_url = f"{external_info.mailerlite_api_url}/subscribers?limit=0"
        headers = MailerLiteClient.generate_headers(external_info)

        resp = requests.get(full_url, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        return resp_json['total']
    
    @staticmethod
    def fetch_all_subscribers_as_list(external_info: ExternalInfo, limit: int = 100) -> List[Dict[str, Any]]:
        all_subs: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        params = {"limit": limit}
        headers = MailerLiteClient.generate_headers(external_info)

        while True:
            if cursor:
                params["cursor"] = cursor

            resp = requests.get(f"{external_info.mailerlite_api_url}/subscribers", headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # collect page items
            all_subs.extend(data["data"])

            # determine next cursor
            meta = data.get("meta")
            next_cursor = meta.get("next_cursor")

            if not next_cursor:
                break
            cursor = next_cursor

        return all_subs

