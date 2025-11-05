from datetime import date, datetime, timezone
import json
import requests

from external_info import ExternalInfo

class MondayComClient:
    @staticmethod
    def add_datapoint(external_info: ExternalInfo, update_key: str, metric: int):
        # Find the issues we need to update
        # We will need to rely on an existing entry with this field for this item due to this lacking a "work item" and groups having to have the same schema if they are in the same board
        # TODO:  Technically, we should be doing pagination via cursor but to get this online quickly, we can do this later.  We use limit:1 to get the single item.  It should be fine since we are filtering to the UpdateKey which *should* only be mapped to one metric.  Essentially, the UpdateKey should represent what we get from our data source (such as Google Analytics)
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
        resp_json = MondayComClient.search_issues(query=query, external_info=external_info)
        # Theoretically, we should get the distinct list of KRNames that we need to create an entry for.  We should only get one though (read the TODO: above about lack of pagination) so we can just grab the first one.
        kr_name = resp_json['data']['items_page_by_column_values']['items'][0]['name']
        # Reuse the existing TargetValue
        column_values = resp_json['data']['items_page_by_column_values']['items'][0]['column_values']
        target_value = int(list(filter(lambda x: x['id'] == external_info.monday_com_okr_items_targetvalue_column_id, column_values))[0]['text'])

        print(f"KeyResult to update: {kr_name}")

        MondayComClient.create_okr_entry(kr_name=kr_name, current_value=metric, target_value=target_value, update_key=update_key, external_info=external_info)

    @staticmethod
    def search_issues(query, external_info):
        headers = \
        {
            "Authorization": external_info.monday_com_api_token,
            "Content-Type": "application/json"
        }

        resp = requests.post(external_info.monday_com_api_url, json={"query": query}, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        return resp_json
    
    @staticmethod
    def create_okr_entry(kr_name: str, current_value: int, target_value: int, update_key: str, external_info):
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