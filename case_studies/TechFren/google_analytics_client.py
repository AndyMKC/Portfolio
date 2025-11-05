import json

from external_info import ExternalInfo
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

class GoogleAnalyticsClient:
    @staticmethod
    def get_ga4_service_account_credentials(external_info: ExternalInfo) -> service_account.Credentials:        
        creds = service_account.Credentials.from_service_account_info(
            json.loads(external_info.google_cloud_cred),
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )

        return creds

    @staticmethod
    def fetch_ga4_metric(external_info: ExternalInfo, r_window: int, metric_name: str) -> int:
        creds = GoogleAnalyticsClient.get_ga4_service_account_credentials(external_info)
        client = BetaAnalyticsDataClient(credentials=creds)
        request = RunReportRequest(
            property=f"properties/{external_info.ga4_property_id}",
            date_ranges=[DateRange(start_date=f"{r_window}daysAgo", end_date="today")],
            metrics=[Metric(name=metric_name)]
        )
        response = client.run_report(request)
        # pick a metric value: if no rows, treat as zero
        if response.rows:
            # assume first metric of first row
            val = response.rows[0].metric_values[0].value
            return int(float(val))
        return 0