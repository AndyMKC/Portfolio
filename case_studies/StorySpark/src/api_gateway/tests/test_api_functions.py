import json
import pytest
from azure.functions import HttpRequest, HttpResponse
import inspect

# Import your handler functions
from AddBookFunction.__init__ import main as add_book
from GetBookRecommendationFunction.__init__ import main as get_recommendations
from MarkBookReadFunction.__init__ import main as mark_read
from RemoveBookFunction.__init__ import main as remove_book
from z_HealthFunction.__init__ import main as health_check

def make_request(method: str, url: str, params: dict = None, body: dict = None):
    return HttpRequest(
        method=method,
        url=url,
        params=params or {},
        body=json.dumps(body or {}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    return resp

def validate_request(resp: HttpResponse):
    print("************************************")
    print(f"Current test function name: {inspect.stack()[1].function}")
    print(f"Response body: {resp.get_body().decode()}")
    assert resp.status_code == 200
    print("************************************")

def test_health_check():
    req = make_request("GET", "/api/health")
    resp = health_check(req)
    validate_request(resp)

def test_get_recommendations():
    params = {"ownerId": "alice", "subjects": "math,science"}
    req = make_request("GET", "/api/books/getRecommendations", params=params)
    resp = get_recommendations(req)
    validate_request(resp)

def test_add_and_remove_book():
    add_params = {"ownerId": "alice", "isbn13": "9781234567897"}
    req_add = make_request("POST", "/api/books/add", params=add_params)
    resp_add = add_book(req_add)
    validate_request(resp_add)

    req_rem = make_request("DELETE", "/api/books/remove", params=add_params)
    resp_rem = remove_book(req_rem)
    validate_request(resp_rem)

def test_mark_book_read():
    params = {
        "ownerId": "alice",
        "isbn13": "9781234567897",
        "datetimeRead": "2025-09-19T16:05:00"
    }
    req = make_request("POST", "/api/books/markRead", params=params)
    resp = mark_read(req)
    validate_request(resp)