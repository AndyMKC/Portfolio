# https://storysparkapigateway.azurewebsites.net/api/books/add
import azure.functions as func
import json

from services.metadata_gatherer import gather_metadata

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Read query parameters
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

    try:
        per_source = gather_metadata(isbn)
    except Exception as ex:
        logging.error("Metadata gatherer failed: %s", ex)
        return func.HttpResponse(
            "Failed to collect metadata", status_code=502
        )


    # Stub logic: echo back the values
    response_payload = {
        "ownerId": owner_id,
        "isbn": isbn,
        "message": "Book-add stub received"
    }

    return func.HttpResponse(
        json.dumps(response_payload),
        status_code=200,
        mimetype="application/json"
    )