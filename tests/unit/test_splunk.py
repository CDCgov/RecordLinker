import unittest.mock

import pytest

from recordlinker import splunk


class TestSplunkHECClient:
    def test_invalid_uri(self):
        with pytest.raises(splunk.SplunkError):
            splunk.SplunkHECClient("http://localhost")

    def test_valid_uri(self):
        with unittest.mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = unittest.mock.MagicMock()
            mock_response.read.return_value = b"{}"
            mock_response.getcode.return_value = 400  # Set getcode() to return 400
            mock_urlopen.return_value.__enter__.return_value = mock_response
            client = splunk.SplunkHECClient("splunkhec://token@localhost:8088?index=idx&source=src")
            assert client.url == "https://localhost:8088/services/collector/event"
            assert client.headers == {
                "Authorization": "Splunk token",
                "Content-Type": "application/json",
            }
            assert client.params == {"host": "localhost", "sourcetype": "_json", "index": "idx", "source": "src"}

    def test_valid_uri_no_port(self):
        with unittest.mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = unittest.mock.MagicMock()
            mock_response.read.return_value = b"{}"
            mock_response.getcode.return_value = 400  # Set getcode() to return 400
            mock_urlopen.return_value.__enter__.return_value = mock_response
            client = splunk.SplunkHECClient("splunkhec://token@localhost?index=idx&source=src")
            assert client.url == "https://localhost/services/collector/event"
            assert client.headers == {
                "Authorization": "Splunk token",
                "Content-Type": "application/json",
            }
            assert client.params == {"host": "localhost", "sourcetype": "_json", "index": "idx", "source": "src"}

    def test_send(self):
        with unittest.mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = unittest.mock.MagicMock()
            mock_response.read.return_value = b"{}"
            mock_response.getcode.side_effect = [400, 200]  # Set getcode() to return 400
            mock_urlopen.return_value.__enter__.return_value = mock_response
            client = splunk.SplunkHECClient("splunkhec://token@localhost?index=idx&source=src")
            assert client.send({"key": "value"}, epoch=10.5) == 200
            req = mock_urlopen.call_args[0][0]
            assert req.method == "POST"
            assert req.get_full_url() == "https://localhost/services/collector/event"
            assert req.headers == {
                "Authorization": "Splunk token",
                "Content-type": "application/json",
            }
            assert req.data == b'{"time": 10.5, "event": {"key": "value"}, "host": "localhost", "sourcetype": "_json", "index": "idx", "source": "src"}'
