import os
#import base64
import json
import requests
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

def get_ga4_service_account_credentials(login_info):        
    creds = service_account.Credentials.from_service_account_info(
        json.loads(login_info.google_cloud_cred),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )

    return creds

def fetch_ga4_metric(login_info, r_window, metric_name):
    creds = get_ga4_service_account_credentials(login_info)
    client = BetaAnalyticsDataClient(credentials=creds)
    request = RunReportRequest(
        property=f"properties/{login_info.ga4_property_id}",
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

def jira_search_issues(jql, login_info):   
    url = f"{login_info.jira_base}/rest/api/3/search/jql"
    auth = (login_info.jira_user, login_info.jira_api_token)
    params = {"jql": jql, "fields": "key,summary,assignee,priority,reporter,labels", "maxResults": 100}
    r = requests.get(url, auth=auth, params=params)
    r.raise_for_status()
    data = r.json()
    return [i["key"] for i in data.get("issues", [])]

def update_jira_field(issue_key, value, login_info):
    url = f"{login_info.jira_base}/rest/api/3/issue/{issue_key}"
    auth = (login_info.jira_user, login_info.jira_api_token)

    # We cannot use "KR Current" since it is a custom field so we have to use the underlying id
    # # To see which custom field id is mapped to KR Current, use this:
    # # curl -u "<use your email here -- for example amcheng@umich.edu>:<use your token here>" -X GET "https://andymkc.atlassian.net/rest/api/3/field" -H "Accept: application/json"
    kr_current_custo_field_id = "customfield_10060"
    payload = {"fields": {kr_current_custo_field_id: value}}
    r = requests.put(url, auth=auth, json=payload)
    r.raise_for_status()
    return r.status_code

def update_active_users_okr(login_info):
    # Get the metric value
    r_window = 7
    metric_name = "activeUsers"
    metric = fetch_ga4_metric(login_info, r_window, metric_name)
    print("GA4 metric:", metric)

    # Find the issues we need to update
    # We will use tags to see which Stories we need to update
    jql = f'project = "TECHFREN" AND issuetype = Story AND labels = "R{r_window}_ActiveUsers"' 
    issues = jira_search_issues(jql, login_info)
    print("Issues to update:", issues)

    for k in issues:
        status = update_jira_field(k, metric, login_info)
        print("Updated", k, "status", status)

def main():
    # Harvest things from the OS environment
    class LoginInfo:
        # Load config from environment (GitHub Actions variables/secrets are exposed as env vars)
        google_cloud_cred = os.environ.get("TECHFREN_GOOGLE_CLOUD_CRED")
        # This is from the Google Analytics Admin -> Property page (upper right hand corner)
        ga4_property_id = os.environ.get("TECHFREN_GA4_PROPERTY_ID")
        jira_base = os.environ.get("TECHFREN_JIRA_BASE")
        # TODO:  Make a new robot account for this
        jira_user = os.environ.get("TECHFREN_JIRA_USER")
        # https://id.atlassian.com -> security -> create and manage API tokens
        jira_api_token = os.environ.get("TECHFREN_JIRA_API_TOKEN")  # secret
    
    login_info = LoginInfo()
    # Basic validation
    missing = [name for name, val in [
        ("TECHFREN_GOOGLE_CLOUD_CRED", login_info.google_cloud_cred),
        ("TECHFREN_GA4_PROPERTY_ID", login_info.ga4_property_id),
        ("TECHFREN_JIRA_BASE", login_info.jira_base),
        ("TECHFREN_JIRA_USER", login_info.jira_user),
        ("TECHFREN_JIRA_API_TOKEN", login_info.jira_api_token),
    ] if not val]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    
    update_active_users_okr(login_info)

if __name__ == "__main__":
    main()

