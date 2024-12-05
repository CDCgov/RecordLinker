import json
import time
import typing
import urllib.parse
import urllib.request
import uuid

TIMEOUT = 5


class SplunkError(Exception):
    pass


class SplunkHECClient:
    PATH = "/services/collector/event"

    def __init__(self, splunk_uri: str) -> None:
        """
        Create a new Splunk HEC client and test its connection.
        The URI uses a custom scheme to specify the Splunk HEC server and parameters.
        The URI format is:
            splunkhec://<token>@<host>:<port>?index=<index>&proto=<protocol>&source=<source>
        """
        try:
            uri: urllib.parse.ParseResult = urllib.parse.urlparse(splunk_uri)
            # flatten the query string values from lists to single values
            qs: dict[str, str] = {k: v[0] for k, v in urllib.parse.parse_qs(uri.query).items()}

            if uri.scheme != "splunkhec":
                raise SplunkError(f"invalid scheme: {uri.scheme}")

            scheme = qs.get("proto", "https").lower()
            host = f"{uri.hostname}:{uri.port}" if uri.port else uri.hostname
            self.url = f"{scheme}://{host}{self.PATH}"
            self.headers = {
                "Authorization": f"Splunk {uri.username}",
                "Content-type": "application/json",
                # There is no intention of using HEC index acknowledgments to follow up on events,
                # however in the case that the Splunk administrator has enabled this feature on the
                # HEC token, just pass a random UUID back as the channel so the request is accepted.
                # When index acknowledgments are disabled, this header is ignored.
                "X-splunk-request-channel": str(uuid.uuid4()),
            }
            # initialize the default payload parameters
            self.params: dict[str, str] = {"host": uri.hostname or "", "sourcetype": "_json"}
            if qs.get("index"):
                self.params["index"] = qs["index"]
            if qs.get("source"):
                self.params["source"] = qs["source"]
            self._test_connection()
        except Exception as exc:
            raise SplunkError(f"invalid connection: {splunk_uri}") from exc

    def _send_request(self, body: bytes | None = None):
        request = urllib.request.Request(self.url, data=body, method="POST", headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                # return the response status code
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code

    def _test_connection(self) -> None:
        status = self._send_request()
        # check for a 400 bad request, which indicates a successful connection
        # 400 is expected because the payload is empty
        if status != 400:
            raise urllib.error.HTTPError(self.url, status, "could not connect", None, None)  # type: ignore

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
        try:
            return self._send_request(body=body)
        except Exception as exc:
            raise SplunkError(f"could not send data: {data}") from exc
