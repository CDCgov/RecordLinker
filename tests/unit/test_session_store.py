import fastapi

from recordlinker import session_store


def test_save_session():
    response = fastapi.Response()
    data = {"test": "data"}
    assert 'set-cookie' not in response.headers
    session_store.save_session(response, "test-session", data)
    assert 'set-cookie' in response.headers
    assert response.headers["set-cookie"].startswith("test-session=")

def test_load_session():
    response = fastapi.Response()
    session_store.save_session(response, "test-session", {"test": "data"})
    session_id = response.headers["set-cookie"].split(" ")[0].split("=")[1]
    scope = {
        "type": "http",
        "headers": [
            (b"cookie", f"test-session={session_id}".encode("latin-1"))
        ],
    }
    request = fastapi.Request(scope=scope)
    assert session_store.load_session(request, "test-session") == {"test": "data"}
    assert session_store.load_session(request, "invalid-session") is None
