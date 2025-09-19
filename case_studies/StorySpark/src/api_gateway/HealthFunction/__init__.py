# https://storysparkapigateway.azurewebsites.net/api/health
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("SeeDawBelly", status_code=200)