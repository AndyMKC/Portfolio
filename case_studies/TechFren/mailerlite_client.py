import requests

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