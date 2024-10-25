import json
import time
import typing
import urllib.parse
import urllib.request

TIMEOUT = 5


class SplunkHECClient:
    PATH = "/services/collector/event"

    def __init__(self, splunk_uri: str) -> None:
        """
        Create a new Splunk HEC client and test its connection.
        The URI uses a custom scheme to specify the Splunk HEC server and parameters.
        The URI format is:
            splunkhec://<token>@<host>:<port>?index=<index>&proto=<protocol>&ssl_verify=<verify>&source=<source>
        """
        uri: urllib.parse.ParseResult = urllib.parse.urlparse(splunk_uri)
        # flatten the query string values from lists to single values
        qs: dict[str, str] = {k: v[0] for k, v in urllib.parse.parse_qs(uri.query).items()}

        scheme = qs.get("proto", "https").lower()
        self.url = f"{scheme}://{uri.hostname}:{uri.port}{self.PATH}"
        self.headers = {
            "Authorization": f"Splunk {uri.username}",
            "Content-Type": "application/json",
        }
        # initialize the default payload parameters
        self.params: dict[str, str] = {"host": uri.hostname or "", "sourcetype": "_json"}
        if qs.get("index"):
            self.params["index"] = qs["index"]
        if qs.get("source"):
            self.params["source"] = qs["source"]
        self._test_connection()

    def _send_request(self, body: bytes | None = None):
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
            raise urllib.error.HTTPError(self.url, status, "could not connect", None, None)  # type: ignore

    # TODO: tests cases
    def send(self, data: dict, epoch: float = 0) -> int:
        """
        Send data to the Splunk HEC endpoint.

        :param data: The data to send.
        :param epoch: The timestamp to use for the event. If not provided, the current time is used.
        :return: The HTTP status code of the response.
        """
        epoch = epoch or int(time.time())
        payload: dict[str, typing.Any] = {"time": epoch, "event": data} | self.params
        body: bytes = json.dumps(payload).encode("utf-8")
        return self._send_request(body=body)
