import fastapi
import itsdangerous

from recordlinker import cookie_store
from recordlinker.config import settings


def test_save_cookie():
    response = fastapi.Response()
    data = {"test": "data"}
    assert "set-cookie" not in response.headers
    cookie_store.save_cookie(response, "test-session", data)
    assert "set-cookie" in response.headers
    assert response.headers["set-cookie"].startswith("test-session=")
    val = response.headers["set-cookie"].split(";")[0].split("=")[1]
    assert val == itsdangerous.URLSafeSerializer(settings.secret_key).dumps(data)


def test_load_cookie():
    response = fastapi.Response()
    cookie_store.save_cookie(response, "test-session", {"test": "data"})
    session_id = response.headers["set-cookie"].split(" ")[0].split("=")[1]
    scope = {
        "type": "http",
        "headers": [(b"cookie", f"test-session={session_id}".encode("latin-1"))],
    }
    request = fastapi.Request(scope=scope)
    assert cookie_store.load_cookie(request, "test-session") == {"test": "data"}
    assert cookie_store.load_cookie(request, "invalid-session") is None


def test_reset_cookie():
    response = fastapi.Response()
    assert "set-cookie" not in response.headers
    cookie_store.reset_cookie(response, "test-session")
    assert "set-cookie" in response.headers
    assert response.headers["set-cookie"].startswith("test-session=")

    # Check if the cookie is reset to an empty dictionary
    assert response.headers["set-cookie"].split(";")[0].split("=")[
        1
    ] == itsdangerous.URLSafeSerializer(settings.secret_key).dumps({})
