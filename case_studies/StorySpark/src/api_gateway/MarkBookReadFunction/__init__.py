# https://storysparkapigateway.azurewebsites.net/api/books/markRead

import azure.functions as func
import json
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:

    owner_id = req.params.get("ownerId")
    isbn13   = req.params.get("isbn13")
    datetimeRead_str = req.params.get("datetimeRead")

    if not owner_id or not isbn13 or not datetimeRead_str:
        return func.HttpResponse(
            json.dumps({"error": "Please provide all of ownerId, isbn13 and datetimeRead as query parameters."}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        datetime_read = datetime.fromisoformat(datetimeRead_str)
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "datetimeRead must be ISO-8601 datetime"}),
            status_code=400,
            mimetype="application/json"
        )

    # Stub payload
    response_payload = {
        "ownerId": owner_id,
        "isbn13": isbn13,
        "timeRead": datetime_read.isoformat(),
        "message": "MarkBookReadFunction stub received"
    }

    return func.HttpResponse(
        json.dumps(response_payload),
        status_code=200,
        mimetype="application/json"
    )