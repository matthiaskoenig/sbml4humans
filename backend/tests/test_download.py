"""Tests of the download of the model behind a url."""

import gzip
import http.server
import ipaddress
import threading
import time
from collections.abc import Iterator

import pytest

from sbml4humans import download as download_module
from sbml4humans import limits
from sbml4humans.download import (
    DownloadTimeoutError,
    IPAddress,
    UrlNotAllowedError,
    download,
    is_public,
)
from sbml4humans.limits import ContentTooLargeError
from sbml4humans.resources import REPRESSILATOR_SBML


MODEL = REPRESSILATOR_SBML.read_bytes()
# the name of the test server, which the tests resolve to its address
PUBLIC_HOST = "models.example"
# a name which resolves to an address of the internal network
INTERNAL_HOST = "internal.example"


class _Handler(http.server.BaseHTTPRequestHandler):
    """The answers of the test server, by path."""

    def do_GET(self) -> None:
        """Answer a GET by the path of the request."""
        # the port of the server, which the url of the request names
        port = self.headers["Host"].rsplit(":", 1)[1]
        if self.path == "/model":
            self._send(200, MODEL)
        elif self.path == "/redirect":
            self._redirect(f"http://{PUBLIC_HOST}:{port}/model")
        elif self.path == "/internal":
            self._redirect(f"http://{INTERNAL_HOST}:{port}/model")
        elif self.path == "/file":
            self._redirect("file:///etc/passwd")
        elif self.path == "/loop":
            self._redirect(f"http://{PUBLIC_HOST}:{port}/loop")
        elif self.path == "/large":
            self._send(200, b"x" * 2048)
        elif self.path == "/chunked":
            # no content length: the size is only known while it is read
            self.send_response(200)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            for _ in range(4):
                self.wfile.write(b"200\r\n" + b"x" * 512 + b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        elif self.path == "/bomb":
            body = gzip.compress(b"x" * 4096)
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/slow":
            self.send_response(200)
            self.send_header("Content-Length", "100")
            self.end_headers()
            for _ in range(10):
                self.wfile.write(b"x" * 10)
                self.wfile.flush()
                time.sleep(0.1)
        else:
            self._send(404, b"not found")

    def _send(self, status: int, body: bytes) -> None:
        """Answer with the body."""
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        """Answer with a redirect to the location."""
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Keep the output of the tests clean."""


@pytest.fixture(scope="module")
def server() -> Iterator[int]:
    """A server on a free port of the loopback interface, its port."""
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def resolved(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Resolve the names of the tests, the test server counting as public.

    The test server listens on the loopback interface, which is no public
    address. The names are resolved here, and loopback is public for the test
    server alone, which is the name `PUBLIC_HOST`. Returns the names in the
    order they were resolved.
    """
    names: list[str] = []
    real_resolve = download_module.resolve
    real_is_public = download_module.is_public
    loopback = ipaddress.ip_address("127.0.0.1")

    def resolve(host: str, port: int) -> list[IPAddress]:
        names.append(host)
        if host == PUBLIC_HOST:
            return [loopback]
        if host == INTERNAL_HOST:
            return [ipaddress.ip_address("10.0.0.1")]
        return real_resolve(host, port)

    def public(address: IPAddress) -> bool:
        return (names[-1:] == [PUBLIC_HOST] and address == loopback) or real_is_public(
            address
        )

    monkeypatch.setattr(download_module, "resolve", resolve)
    monkeypatch.setattr(download_module, "is_public", public)
    return names


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "127.1.2.3",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "0.0.0.0",
        "224.0.0.1",
        "240.0.0.1",
        "255.255.255.255",
        "::",
        "::1",
        "fe80::1",
        "fc00::1",
        "ff02::1",
        "::ffff:127.0.0.1",
        "::ffff:10.0.0.1",
        "::ffff:169.254.169.254",
        "2002:7f00:1::",
        "64:ff9b::a00:1",
    ],
)
def test_internal_addresses_are_not_public(address: str) -> None:
    """Loopback, private, link local, shared, reserved, multicast, unspecified."""
    assert not is_public(ipaddress.ip_address(address))


@pytest.mark.parametrize(
    "address", ["8.8.8.8", "141.20.1.1", "2001:4860:4860::8888", "::ffff:8.8.8.8"]
)
def test_public_addresses_are_public(address: str) -> None:
    """The addresses of the internet."""
    assert is_public(ipaddress.ip_address(address))


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.org/model.xml",
        "gopher://example.org/",
        "model.xml",
        "http://",
    ],
)
def test_only_http_is_downloaded(url: str) -> None:
    """Another scheme than http or https, or no host, is refused."""
    with pytest.raises(UrlNotAllowedError):
        download(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:9/",
        "http://localhost:9/",
        "http://[::1]:9/",
        "http://10.0.0.1:9/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::ffff:127.0.0.1]:9/",
        "http://2130706433:9/",
    ],
)
def test_internal_addresses_are_not_downloaded(url: str) -> None:
    """A url of the machine or of its network is refused before it is connected."""
    with pytest.raises(UrlNotAllowedError):
        download(url)


def test_internal_addresses_are_downloaded_when_allowed(
    server: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The end to end tests serve their model on the loopback interface."""
    monkeypatch.setattr(download_module, "ALLOW_PRIVATE_URLS", True)
    assert download(f"http://127.0.0.1:{server}/model") == MODEL
    with pytest.raises(UrlNotAllowedError):
        download("file:///etc/passwd")


def test_a_name_of_an_internal_address_is_not_downloaded(
    server: int, resolved: list[str]
) -> None:
    """The address a name resolves to is checked, not the name."""
    with pytest.raises(UrlNotAllowedError):
        download(f"http://{INTERNAL_HOST}:{server}/model")


def test_a_public_url_is_downloaded(server: int, resolved: list[str]) -> None:
    """The content behind a public url."""
    assert download(f"http://{PUBLIC_HOST}:{server}/model") == MODEL
    assert resolved == [PUBLIC_HOST]


def test_a_redirect_is_followed_and_checked(server: int, resolved: list[str]) -> None:
    """Every redirect is checked like the url itself."""
    assert download(f"http://{PUBLIC_HOST}:{server}/redirect") == MODEL
    with pytest.raises(UrlNotAllowedError):
        download(f"http://{PUBLIC_HOST}:{server}/internal")
    assert resolved[-1] == INTERNAL_HOST
    with pytest.raises(UrlNotAllowedError):
        download(f"http://{PUBLIC_HOST}:{server}/file")


def test_redirects_are_limited(
    server: int, resolved: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A redirect loop ends after `MAX_REDIRECTS`."""
    monkeypatch.setattr(limits, "MAX_REDIRECTS", 3)
    with pytest.raises(UrlNotAllowedError, match="redirects"):
        download(f"http://{PUBLIC_HOST}:{server}/loop")
    assert len(resolved) <= 4


@pytest.mark.parametrize("path", ["/large", "/chunked", "/bomb"])
def test_the_size_is_limited(
    server: int, resolved: list[str], monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    """By the declared length, by the bytes read and after the content encoding."""
    monkeypatch.setattr(limits, "MAX_CONTENT_SIZE", 1024)
    with pytest.raises(ContentTooLargeError):
        download(f"http://{PUBLIC_HOST}:{server}{path}")


def test_the_time_is_limited(
    server: int, resolved: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A server which sends slowly does not hold the download beyond its deadline."""
    monkeypatch.setattr(limits, "DOWNLOAD_TIMEOUT", 0.3)
    with pytest.raises(DownloadTimeoutError):
        download(f"http://{PUBLIC_HOST}:{server}/slow")


def test_an_error_status_fails(server: int, resolved: list[str]) -> None:
    """A url which answers with an error status is no model."""
    with pytest.raises(Exception, match="404"):
        download(f"http://{PUBLIC_HOST}:{server}/missing")
