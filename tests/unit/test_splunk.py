import unittest.mock

import pytest

from recordlinker import splunk


class TestSplunkHECClient:
    def test_invalid_uri(self):
        with pytest.raises(splunk.SplunkError):
            splunk.SplunkHECClient("http://localhost")

    def test_valid_uri(self):
        with unittest.mock.patch("urllib.request.urlopen") as mock_urlopen:
            mresp = unittest.mock.MagicMock(status=400)
            mock_urlopen.return_value.__enter__.return_value = mresp
            client = splunk.SplunkHECClient("splunkhec://token@localhost:8088?index=idx&source=src")
            assert client.url == "https://localhost:8088/services/collector/event"
            assert client.headers["Authorization"] == "Splunk token"
            assert client.headers["Content-type"] == "application/json"
            assert len(client.headers["X-splunk-request-channel"]) == 36
            assert client.params == {"host": "localhost", "sourcetype": "_json", "index": "idx", "source": "src"}

    def test_valid_uri_no_port(self):
        with unittest.mock.patch("urllib.request.urlopen") as mock_urlopen:
            mresp1 = unittest.mock.MagicMock(status=400)
            mresp2 = unittest.mock.MagicMock(status=200)
            mock_urlopen.return_value.__enter__.side_effect = (mresp1, mresp2)
            client = splunk.SplunkHECClient("splunkhec://token@localhost?index=idx&source=src")
            assert client.url == "https://localhost/services/collector/event"
            assert client.headers["Authorization"] == "Splunk token"
            assert client.headers["Content-type"] == "application/json"
            assert len(client.headers["X-splunk-request-channel"]) == 36
            assert client.params == {"host": "localhost", "sourcetype": "_json", "index": "idx", "source": "src"}

    def test_send(self):
        with unittest.mock.patch("urllib.request.urlopen") as mock_urlopen:
            mresp1 = unittest.mock.MagicMock(status=400)
            mresp2 = unittest.mock.MagicMock(status=200)
            mock_urlopen.return_value.__enter__.side_effect = (mresp1, mresp2)
            client = splunk.SplunkHECClient("splunkhec://token@localhost?index=idx&source=src")
            assert client.send({"key": "value"}, epoch=10.5) == 200
            req = mock_urlopen.call_args[0][0]
            assert req.method == "POST"
            assert req.get_full_url() == "https://localhost/services/collector/event"
            assert client.headers["Authorization"] == "Splunk token"
            assert client.headers["Content-type"] == "application/json"
            assert len(client.headers["X-splunk-request-channel"]) == 36
            assert req.data == b'{"time": 10.5, "event": {"key": "value"}, "host": "localhost", "sourcetype": "_json", "index": "idx", "source": "src"}'
