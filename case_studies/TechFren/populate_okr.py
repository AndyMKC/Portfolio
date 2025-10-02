# ga4_to_jira.py
import base64
import json
import requests
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Metric
from google.oauth2 import service_account

# CONFIG - replace values or load from env/secret manager
G4A_SERVICE_ACCOUNT_FILE = "service-account-g4a.json"

# This is from the Google Analytics Admin -> Property page (upper right hand corner)
GA4_PROPERTY_ID = "505834927"  # numeric
JIRA_BASE = "https://andymkc.atlassian.net"
# TODO:  Make a new robot account for this
JIRA_USER = "amcheng@umich.edu"

# We will use tags to see which Stories we need to update
JQL = 'project = "TECHFREN" AND issuetype = Story AND labels = "R28_ActiveUsers"'

# We cannot use "KR Current" since it is a custom field so we have to use the underlying id
# To see which custom field id is mapped to KR Current, use this:
# curl -u "<use your email here -- for example amcheng@umich.edu>:<use your token here>" -X GET "https://andymkc.atlassian.net/rest/api/3/field" -H "Accept: application/json"
KR_CUSTOM_FIELD = "customfield_10060"

def fetch_ga4_metric():
    creds = service_account.Credentials.from_service_account_file(
        G4A_SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )
    client = BetaAnalyticsDataClient(credentials=creds)
    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
        metrics=[Metric(name="activeUsers")]  # change metric to what you need
    )
    response = client.run_report(request)
    # pick a metric value: if no rows, treat as zero
    if response.rows:
        # assume first metric of first row
        val = response.rows[0].metric_values[0].value
        return int(float(val))
    return 0

def jira_search_issues(jql, jira_api_token):   
    url = f"{JIRA_BASE}/rest/api/3/search/jql"
    auth = (JIRA_USER, jira_api_token)
    params = {"jql": jql, "fields": "key,summary,assignee,priority,reporter,labels", "maxResults": 100}
    r = requests.get(url, auth=auth, params=params)
    r.raise_for_status()
    data = r.json()
    return [i["key"] for i in data.get("issues", [])]

def update_jira_field(issue_key, value, jira_api_token):
    url = f"{JIRA_BASE}/rest/api/3/issue/{issue_key}"
    auth = (JIRA_USER, jira_api_token)
    payload = {"fields": {KR_CUSTOM_FIELD: value}}
    r = requests.put(url, auth=auth, json=payload)
    r.raise_for_status()
    return r.status_code

def main():
    # https://id.atlassian.com -> security -> create and manage API tokens
    jira_api_token = input("JIRA_API_TOKEN: ")
    metric = fetch_ga4_metric()
    print("GA4 metric:", metric)
    issues = jira_search_issues(JQL, jira_api_token)
    print("Issues to update:", issues)
    for k in issues:
        status = update_jira_field(k, metric, jira_api_token)
        print("Updated", k, "status", status)

if __name__ == "__main__":
    main()