import unittest.mock

from sqlalchemy.exc import OperationalError


def test_health_check(client):
    actual_response = client.get("/")
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}


def test_health_check_unavailable(client):
    # mock db session to raise exception
    client.session.execute = unittest.mock.Mock(
        side_effect=OperationalError("mock error", None, None)
    )
    actual_response = client.get("/")
    assert actual_response.status_code == 503
    assert actual_response.json() == {"detail": "Service Unavailable"}


def test_openapi(client):
    actual_response = client.get("/openapi.json")
    assert actual_response.status_code == 200
