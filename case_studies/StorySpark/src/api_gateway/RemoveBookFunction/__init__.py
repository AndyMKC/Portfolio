# https://storysparkapigateway.azurewebsites.net/api/books/remove

import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:

    owner_id = req.params.get("ownerId")
    isbn  = req.params.get("isbn")

    # Validate inputs
    missing = []
    if not owner_id:
        missing.append("ownerId")
    if not isbn:
        missing.append("isbn")
    if missing:
        return func.HttpResponse(
            json.dumps({"error": f"Missing parameters: {', '.join(missing)}"}),
            status_code=400,
            mimetype="application/json"
        )

    # Stub logic: echo deletion request
    payload = {
        "ownerId": owner_id,
        "isbn": isbn,
        "message": "RemoveBookFunction stub received"
    }
    return func.HttpResponse(
        json.dumps(payload),
        status_code=200,
        mimetype="application/json"
    )