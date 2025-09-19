# https://storysparkapigateway.azurewebsites.net/api/books/remove

import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    owner_id = req.params.get("ownerid")
    isbn13  = req.params.get("isbn13")

    if not owner_id or not isbn13:
        return func.HttpResponse(
            json.dumps({"error": "Please provide both ownerId and isbn13 as query parameters."}),
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