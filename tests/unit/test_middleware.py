import unittest.mock

import starlette.applications

from recordlinker import middleware


class TestCorrelationIdMiddleware:
    def test_default(self):
        app = starlette.applications.Starlette()
        obj = middleware.CorrelationIdMiddleware(app)
        assert obj.transformer("1234567890") == "1234567890"
        assert obj.transformer("123456789012345678") == "123456789012"

    def test_custom_length(self):
        app = starlette.applications.Starlette()
        obj = middleware.CorrelationIdMiddleware(app, correlation_id_length=4)
        assert obj.transformer("1234567890") == "1234"
        assert obj.transformer("123456789012345678") == "1234"


class TestAccessLogMiddleware:
    def test_dispatch(self, client):
        with unittest.mock.patch("recordlinker.middleware.ACCESS_LOGGER") as mock_logger:
             response = client.get("/api")
        # Verify the response
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
        assert len(mock_logger.info.mock_calls) == 1
        expected = (
            '[%(correlation_id)s] %(client_ip)s - "%(method)s %(path)s '
            'HTTP/%(http_version)s" %(status_code)d %(process_time).2fms'
        )
        assert mock_logger.info.call_args[0][0] == expected
        assert mock_logger.info.call_args[0][1]["client_ip"] == "testclient"
        assert mock_logger.info.call_args[0][1]["method"] == "GET"
        assert mock_logger.info.call_args[0][1]["path"] == "/"
        assert mock_logger.info.call_args[0][1]["http_version"] == "1.1"
        assert mock_logger.info.call_args[0][1]["status_code"] == 200
        assert mock_logger.info.call_args[0][1]["process_time"] > 0
        assert len(mock_logger.info.call_args[0][1]["correlation_id"]) == 12
