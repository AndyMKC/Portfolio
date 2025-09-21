# https://storysparkapigateway.azurewebsites.net/api/books/remove

import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:

    owner_id = req.params.get("ownerId")
    isbn13  = req.params.get("isbn13")

    # Validate inputs
    missing = []
    if not owner_id:
        missing.append("ownerId")
    if not isbn13:
        missing.append("isbn13")
    if missing:
        return func.HttpResponse(
            json.dumps({"error": f"Missing parameters: {', '.join(missing)}"}),
            status_code=400,
            mimetype="application/json"
        )

    # Stub logic: echo deletion request
    payload = {
        "ownerId": owner_id,
        "isbn13": isbn13,
        "message": "RemoveBookFunction stub received"
    }
    return func.HttpResponse(
        json.dumps(payload),
        status_code=200,
        mimetype="application/json"
    )