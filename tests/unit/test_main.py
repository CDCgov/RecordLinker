def test_health_check(client):
    actual_response = client.get("/")
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}


def test_openapi(client):
    actual_response = client.get("/openapi.json")
    assert actual_response.status_code == 200
