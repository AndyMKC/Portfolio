# https://storysparkapigateway.azurewebsites.net/api/books/add
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Read query parameters
    owner_id = req.params.get("ownerId")
    isbn13  = req.params.get("isbn13")

    # Validate inputs
    if not owner_id or not isbn13:
        return func.HttpResponse(
            json.dumps({"error": "Please provide both ownerId and isbn13 as query parameters."}),
            status_code=400,
            mimetype="application/json"
        )

    # Stub logic: echo back the values
    response_payload = {
        "ownerId": owner_id,
        "isbn13": isbn13,
        "message": "Book-add stub received"
    }

    return func.HttpResponse(
        json.dumps(response_payload),
        status_code=200,
        mimetype="application/json"
    )