import os

class ExternalInfo:
    # Load config from environment (GitHub Actions variables/secrets are exposed as env vars)
    google_cloud_cred = os.environ.get("TECHFREN_GOOGLE_CLOUD_CRED")
    # This is from the Google Analytics Admin -> Property page (upper right hand corner)
    ga4_property_id = os.environ.get("TECHFREN_GA4_PROPERTY_ID")

    monday_com_api_token = os.environ.get("TECHFREN_MONDAY_COM_API_TOKEN")
    monday_com_api_url = os.environ.get("TECHFREN_MONDAY_COM_API_URL")
    # Board id you can get from the url.  To get the group id, click on your profile and go to monday labs.  From there, enable developer mode.  Once that is done, you can get the ids from the three dot menu.
    monday_com_okr_items_board_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_BOARD_ID")
    monday_com_okr_items_newsletter_subscribers_group_id =os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_NEWSLETTER_SUBSCRIBERS_GROUP_ID")
    monday_com_okr_items_unique_website_visitors_group_id =os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_UNIQUE_WEBSITE_VISITORS_GROUP_ID")
    monday_com_okr_items_date_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_DATE_COLUMN_ID")
    monday_com_okr_items_currentvalue_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_CURRENTVALUE_COLUMN_ID")
    monday_com_okr_items_targetvalue_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_TARGETVALUE_COLUMN_ID")
    monday_com_okr_items_updatekey_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_UPDATEKEY_COLUMN_ID")

    mailerlite_api_token = os.environ.get("TECHFREN_MAILERLITE_API_TOKEN")
    mailerlite_api_url = os.environ.get("TECHFREN_MAILERLITE_API_URL")