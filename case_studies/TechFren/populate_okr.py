from datetime import date, datetime, timezone
import os
#import base64
import json
import requests

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

def get_ga4_service_account_credentials(external_info):        
    creds = service_account.Credentials.from_service_account_info(
        json.loads(external_info.google_cloud_cred),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )

    return creds

def fetch_ga4_metric(external_info, r_window, metric_name):
    creds = get_ga4_service_account_credentials(external_info)
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

def monday_search_issues(query, external_info):
    headers = \
    {
        "Authorization": external_info.monday_com_api_token,
        "Content-Type": "application/json"
    }

    resp = requests.post(external_info.monday_com_api_url, json={"query": query}, headers=headers)
    resp.raise_for_status()
    resp_json = resp.json()

    return resp_json

def create_monday_item_okr_entry(kr_name: str, current_value: int, target_value: int, update_key: str, external_info):
    headers = \
    {
        "Authorization": external_info.monday_com_api_token,
        "Content-Type": "application/json"
    }
    
    today_utc = datetime.now(timezone.utc).date()
    formatted_utc = today_utc.strftime("%Y-%m-%d")

    new_column_values = {
        # We should not need to fill in the KRName since that is part of the item_name
        external_info.monday_com_okr_items_date_column_id: formatted_utc,
        external_info.monday_com_okr_items_currentvalue_column_id: current_value,
        external_info.monday_com_okr_items_targetvalue_column_id: target_value,
        external_info.monday_com_okr_items_updatekey_column_id: update_key
    }

    mutation = f"""
mutation{{
    create_item(
        board_id:{external_info.monday_com_okr_items_board_id},
        group_id:"{external_info.monday_com_okr_items_group_id}",
        item_name:"{kr_name}",
        column_values:"{json.dumps(new_column_values).replace('"', '\\"')}"
    )
    {{
        id
    }}
}}
"""
    resp = requests.post(external_info.monday_com_api_url, json={"query": mutation}, headers=headers)
    resp.raise_for_status()
    resp_json = resp.json()

    return resp_json

def update_active_users_okr(external_info):
    # Get the metric value
    r_window = 7
    metric_name = "activeUsers"
    metric = fetch_ga4_metric(external_info, r_window, metric_name)
    print("GA4 metric:", metric)

    # Find the issues we need to update
    # We will need to rely on an existing entry with this field for this item due to this lacking a "work item" and groups having to have the same schema if they are in the same board
    # TODO:  Technically, we should be doing pagination via cursor but to get this online quickly, we can do this later.  We use limit:1 to get the single item.  It should be fine since we are filtering to the UpdateKey which *should* only be mapped to one metric.  Essentially, the UpdateKey should represent what we get from our data source (such as Google Analytics)
    update_key = "R7_Unique_Website_Visitors"
    query = f"""
query {{
items_page_by_column_values(
    limit:1
    board_id: {external_info.monday_com_okr_items_board_id}
    columns: [
    {{
        column_id: "{external_info.monday_com_okr_items_updatekey_column_id}",
        column_values: ["{update_key}"]
    }}
    ])
    {{
        items {{
        id
        name,
        group {{ id }}
        column_values(ids: ["{external_info.monday_com_okr_items_targetvalue_column_id}",]) {{
            id
            text
            value
        }}
        }}
    }}
}}
"""
    resp_json = monday_search_issues(query=query, external_info=external_info)
    # Theoretically, we should get the distinct list of KRNames that we need to create an entry for.  We should only get one though (read the TODO: above about lack of pagination) so we can just grab the first one.
    kr_name = resp_json['data']['items_page_by_column_values']['items'][0]['name']
    # Reuse the existing TargetValue
    column_values = resp_json['data']['items_page_by_column_values']['items'][0]['column_values']
    target_value = int(list(filter(lambda x: x['id'] == external_info.monday_com_okr_items_targetvalue_column_id, column_values))[0]['text'])

    print(f"KeyResult to update: {kr_name}")

    create_monday_item_okr_entry(kr_name=kr_name, current_value=metric, target_value=target_value, update_key=update_key, external_info=external_info)

def main():
    # Harvest things from the OS environment
    class ExternalInfo:
        # Load config from environment (GitHub Actions variables/secrets are exposed as env vars)
        google_cloud_cred = os.environ.get("TECHFREN_GOOGLE_CLOUD_CRED")
        # This is from the Google Analytics Admin -> Property page (upper right hand corner)
        ga4_property_id = os.environ.get("TECHFREN_GA4_PROPERTY_ID")

        monday_com_api_token = os.environ.get("TECHFREN_MONDAY_COM_API_TOKEN")
        monday_com_api_url = os.environ.get("TECHFREN_MONDAY_COM_API_URL")
        # Board id you can get from the url.  To get the group id, click on your profile and go to monday labs.  From there, enable developer mode.  Once that is done, you can get the ids from the three dot menu.
        monday_com_okr_items_board_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_BOARD_ID")
        monday_com_okr_items_group_id =os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_GROUP_ID")
        monday_com_okr_items_date_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_DATE_COLUMN_ID")
        monday_com_okr_items_currentvalue_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_CURRENTVALUE_COLUMN_ID")
        monday_com_okr_items_targetvalue_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_TARGETVALUE_COLUMN_ID")
        monday_com_okr_items_updatekey_column_id = os.environ.get("TECHFREN_MONDAY_COM_OKR_ITEMS_UPDATEKEY_COLUMN_ID")
        
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
        ("TECHFREN_MONDAY_COM_OKR_ITEMS_UPDATEKEY_COLUMN_ID", external_info.monday_com_okr_items_updatekey_column_id)
        
    ] if not val]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    
    update_active_users_okr(external_info)

if __name__ == "__main__":
    main()

