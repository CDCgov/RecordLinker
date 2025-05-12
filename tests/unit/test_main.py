import unittest.mock

from sqlalchemy.exc import OperationalError


def test_api_root(client):
    api_root_url = client.app.url_path_for("api:root")
    actual_response = client.get(api_root_url, follow_redirects=False)
    assert actual_response.status_code == 307
    assert actual_response.headers["Location"] == client.app.url_path_for("api:redoc_html")


def test_health_check(client):
    health_url = client.app.url_path_for("api:health-check")
    actual_response = client.get(health_url)
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}


def test_health_check_unavailable(client):
    # mock db session to raise exception
    client.session.execute = unittest.mock.Mock(
        side_effect=OperationalError("mock error", None, None)
    )
    health_url = client.app.url_path_for("api:health-check")
    actual_response = client.get(health_url)
    assert actual_response.status_code == 503
    assert actual_response.json() == {"detail": "Service Unavailable"}


def test_openapi(client):
    openapi_url = client.app.url_path_for("api:openapi")
    actual_response = client.get(openapi_url)
    assert actual_response.status_code == 200

def test_static_assets_not_found_when_ui_static_dir_unset(client):
    static_bundles_response = client.get("/_next/dummy_bundle.css")
    assert static_bundles_response.status_code == 404
    landing_page_response = client.get("/index.html")
    assert landing_page_response.status_code == 404
    wizard_page_response = client.get("/wizard.html")
    assert wizard_page_response.status_code == 404
