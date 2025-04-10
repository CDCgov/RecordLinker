import unittest.mock

from sqlalchemy.exc import OperationalError


def test_health_check(client):
    health_url = client.app.url_path_for("health-check")
    actual_response = client.get(health_url)
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}


def test_health_check_unavailable(client):
    # mock db session to raise exception
    client.session.execute = unittest.mock.Mock(
        side_effect=OperationalError("mock error", None, None)
    )
    health_url = client.app.url_path_for("health-check")
    actual_response = client.get(health_url)
    assert actual_response.status_code == 503
    assert actual_response.json() == {"detail": "Service Unavailable"}


def test_openapi(client):
    actual_response = client.get(client.app.openapi_url)
    assert actual_response.status_code == 200
