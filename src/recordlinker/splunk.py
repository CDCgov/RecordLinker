import concurrent.futures
import json
import time
import typing
import urllib.parse
import urllib.request

TIMEOUT = 5
MAX_WORKERS = 10


class SplunkHECClient:
    PATH = "/services/collector/event"

    def __init__(self, splunk_uri: str) -> None:
        """
        Create a new Splunk HEC client and test its connection.
        The URI uses a custom scheme to specify the Splunk HEC server and parameters.
        The URI format is:
            splunkhec://<token>@<host>:<port>?index=<index>&proto=<protocol>&ssl_verify=<verify>&source=<source>
        """
        uri = urllib.parse.urlparse(splunk_uri)
        qs = urllib.parse.parse_qs(uri.query)
        qs = {k: v[0] for k, v in qs.items()}

        scheme = qs.get("proto", "https").lower()
        self.url = f"{scheme}://{uri.hostname}:{uri.port}{self.PATH}"
        self.headers = {
            "Authorization": f"Splunk {uri.username}",
            "Content-Type": "application/json",
        }
        # initialize the default payload parameters
        self.params: dict[str, str] = {"host": uri.hostname, "sourcetype": "_json"}
        if qs.get("index"):
            self.params["index"] = qs["index"]
        if qs.get("source"):
            self.params["source"] = qs["source"]
        # test the connection
        self._test_connection()

    def _send_request(self, body=None):
        """Function to send HTTP request using urllib and return the response."""
        request = urllib.request.Request(self.url, data=body, method="POST", headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                # return the response status code
                return response.getcode()
        except urllib.error.HTTPError as exc:
            return exc.code

    def _test_connection(self) -> None:
        status = self._send_request()
        # check for a 400 bad request, which indicates a successful connection
        # 400 is expected because the payload is empty
        if status != 400:
            raise urllib.error.HTTPError(self.url, status, "could not connect", None, None)

    # TODO: tests cases
    def send(self, data: dict, epoch: float = 0) -> None:
        """
        Send data to the Splunk HEC endpoint.

        :param data: The data to send.
        :param epoch: The timestamp to use for the event. If not provided, the current time is used.
        """
        epoch = epoch or int(time.time())
        payload: dict[str, typing.Any] = {"time": epoch, "event": data} | self.params
        data: str = json.dumps(payload).encode("utf-8")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # fire and forget
            executor.submit(self._send_request, body=data)
