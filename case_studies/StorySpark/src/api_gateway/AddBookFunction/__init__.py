# https://storysparkapigateway.azurewebsites.net/api/books/add
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Read query parameters
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