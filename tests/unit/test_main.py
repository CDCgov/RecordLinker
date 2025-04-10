import unittest.mock

from sqlalchemy.exc import OperationalError


def test_health_check(client):
    actual_response = client.get("/api")
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}


def test_health_check_unavailable(client):
    # mock db session to raise exception
    client.session.execute = unittest.mock.Mock(
        side_effect=OperationalError("mock error", None, None)
    )
    actual_response = client.get("/api")
    assert actual_response.status_code == 503
    assert actual_response.json() == {"detail": "Service Unavailable"}


def test_openapi(client):
    actual_response = client.get("/api/openapi.json")
    assert actual_response.status_code == 200

def test_static_assets_not_found_when_ui_static_dir_unset(client):
    static_bundles_response = client.get("/_next/dummy_bundle.css")
    assert static_bundles_response.status_code == 404
    landing_page_response = client.get("/index.html")
    assert landing_page_response.status_code == 404
    wizard_page_response = client.get("/wizard.html")
    assert wizard_page_response.status_code == 404
