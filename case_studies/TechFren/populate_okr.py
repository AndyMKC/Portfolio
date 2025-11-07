from external_info import ExternalInfo
from google_analytics_client import GoogleAnalyticsClient
from mailerlite_client import MailerLiteClient
from monday_com_client import MondayComClient

def update_unique_website_visitors_okr(external_info):
    print("************ Start:  Updating Unique Website Visitors OKR ************")
    # Get the metric value
    r_window = 7
    metric_name = "activeUsers"
    metric = GoogleAnalyticsClient.fetch_ga4_metric(external_info, r_window, metric_name)
    print("Metric:", metric)

    # Update the OKR
    update_key = "R7_Unique_Website_Visitors"
    MondayComClient.add_datapoint(external_info=external_info,
                                  update_key=update_key,
                                  metric=metric,
                                  group_id=external_info.monday_com_okr_items_unique_website_visitors_group_id)
    print("************ End:  Updating Unique Website Visitors OKR ************")

def update_newsletter_subscribers_okr(external_info):
    print("************ Start:  Updating Newsletter Subscribers OKR ************")
    # Get the list of all subscribers
    subscribers = MailerLiteClient.fetch_all_subscribers_as_list(external_info)
    
    # Not all subscribers are active.  On the website, this includes people that are unsubscribed, bounced, complained about this being spam, and unconfirmed.
    # For this, let's count only the Active people
    active_subscribers = list(filter(lambda x: x['status'].lower() == 'active', subscribers))
    metric = len(active_subscribers)
    print("Metric:", metric)    

    # Update the OKR
    update_key = "Newsletter_Subscribers"
    MondayComClient.add_datapoint(external_info=external_info,
                                  update_key=update_key,
                                  metric=metric,
                                  group_id=external_info.monday_com_okr_items_newsletter_subscribers_group_id)
    print("************ End:  Updating Newsletter Subscribers OKR ************")

def main():       
    external_info = ExternalInfo()
    
    # Basic validation
    missing = [name for name, val in [
        ("TECHFREN_GOOGLE_CLOUD_CRED", external_info.google_cloud_cred),
        ("TECHFREN_GA4_PROPERTY_ID", external_info.ga4_property_id),
        ("TECHFREN_MONDAY_COM_API_TOKEN", external_info.monday_com_api_token),
        ("TECHFREN_MONDAY_COM_API_URL", external_info.monday_com_api_url),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_BOARD_ID", external_info.monday_com_okr_items_board_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_NEWSLETTER_SUBSCRIBERS_GROUP_ID", external_info.monday_com_okr_items_newsletter_subscribers_group_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_UNIQUE_WEBSITE_VISITORS_GROUP_ID", external_info.monday_com_okr_items_unique_website_visitors_group_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_DATE_COLUMN_ID", external_info.monday_com_okr_items_date_column_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_CURRENTVALUE_COLUMN_ID", external_info.monday_com_okr_items_currentvalue_column_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_TARGETVALUE_COLUMN_ID", external_info.monday_com_okr_items_targetvalue_column_id),
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_UPDATEKEY_COLUMN_ID", external_info.monday_com_okr_items_updatekey_column_id),
        ("TECHFREN_MAILERLITE_API_TOKEN", external_info.mailerlite_api_token),
        ("TECHFREN_MAILERLITE_API_URL", external_info.mailerlite_api_url)
        
    ] if not val]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    
    update_unique_website_visitors_okr(external_info)
    update_newsletter_subscribers_okr(external_info)

if __name__ == "__main__":
    main()

