import os

from external_info import ExternalInfo
from google_analytics_client import GoogleAnalyticsClient
from monday_com_client import MondayComClient

def update_active_users_okr(external_info):
    # Get the metric value
    r_window = 7
    metric_name = "activeUsers"
    metric = GoogleAnalyticsClient.fetch_ga4_metric(external_info, r_window, metric_name)
    print("GA4 metric:", metric)

    update_key = "R7_Unique_Website_Visitors"
    MondayComClient.add_datapoint(external_info=external_info, update_key=update_key, metric=metric)

def main():       
    external_info = ExternalInfo()
    
    # Basic validation
    missing = [name for name, val in [
        ("TECHFREN_GOOGLE_CLOUD_CRED", external_info.google_cloud_cred),
        ("TECHFREN_GA4_PROPERTY_ID", external_info.ga4_property_id),
        ("TECHFREN_MONDAY_COM_API_TOKEN", external_info.monday_com_api_token),
        ("TECHFREN_MONDAY_COM_API_URL", external_info.monday_com_api_url),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_BOARD_ID", external_info.monday_com_okr_items_board_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_GROUP_ID", external_info.monday_com_okr_items_group_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_DATE_COLUMN_ID", external_info.monday_com_okr_items_date_column_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_CURRENTVALUE_COLUMN_ID", external_info.monday_com_okr_items_currentvalue_column_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_TARGETVALUE_COLUMN_ID", external_info.monday_com_okr_items_targetvalue_column_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_UPDATEKEY_COLUMN_ID", external_info.monday_com_okr_items_updatekey_column_id),
        ("TECHFREN_MAILERLITE_API_TOKEN", external_info.mailerlite_api_token)
        
    ] if not val]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    
    update_active_users_okr(external_info)

if __name__ == "__main__":
    main()

