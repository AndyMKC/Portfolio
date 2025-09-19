# https://storysparkapigateway.azurewebsites.net/api/books/getRecommendations
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    owner_id = req.params.get("ownerId")
    subjects_raw = req.params.get("subjects")

    # Validate inputs
    missing = []
    if not owner_id:
        missing.append("ownerId")
    if not subjects_raw:
        missing.append("subjects")
    if missing:
        return func.HttpResponse(
            json.dumps({"error": f"Missing parameters: {', '.join(missing)}"}),
            status_code=400,
            mimetype="application/json"
        )

    # Parse subjects into a list
    subjects = [s.strip() for s in subjects_raw.split(",") if s.strip()]

    # Stub recommendations payload
    recommendations = [
        {"id": "1", "title": f"Sample {subjects[0]} Book"} if subjects else {"id": "1", "title": "Sample Book A"},
        {"id": "2", "title": "Sample Book B"}
    ]

    response_payload = {
        "ownerId": owner_id,
        "subjects": subjects,
        "recommendations": recommendations
    }

    return func.HttpResponse(
        json.dumps(response_payload),
        status_code=200,
        mimetype="application/json"
    )