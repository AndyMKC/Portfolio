# https://storysparkapigateway.azurewebsites.net/api/books/markRead

import azure.functions as func
import json
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:

    owner_id = req.params.get("ownerId")
    isbn   = req.params.get("isbn")
    datetimeRead_str = req.params.get("datetimeRead")

    # Validate inputs
    missing = []
    if not owner_id:
        missing.append("ownerId")
    if not isbn:
        missing.append("isbn")
    if not datetimeRead_str:
        missing.append("datetimeRead")
    if missing:
        return func.HttpResponse(
            json.dumps({"error": f"Missing parameters: {', '.join(missing)}"}),
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
        "isbn": isbn,
        "timeRead": datetime_read.isoformat(),
        "message": "MarkBookReadFunction stub received"
    }

    return func.HttpResponse(
        json.dumps(response_payload),
        status_code=200,
        mimetype="application/json"
    )