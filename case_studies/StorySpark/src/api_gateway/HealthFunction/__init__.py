# https://storysparkapigateway.azurewebsites.net/api/health
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    raise ValueError("QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ")
    #return func.HttpResponse("OK", status_code=200)