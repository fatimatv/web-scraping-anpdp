import pytest
import requests

from anpd_monitor.http_client import HttpClient, HttpClientError, check_robots_allowed


class FakeSession:
    def __init__(self, responses=None, error=None):
        self.headers = {}
        self.responses = list(responses or [])
        self.error = error
        self.calls = 0

    def request(self, method, url, timeout):
        self.calls += 1
        if self.error:
            raise self.error
        return self.responses.pop(0)


def response(status=200, content=b"ok"):
    item = requests.Response()
    item.status_code = status
    item._content = content
    item.url = "https://example.test"
    return item


def test_http_client_sets_user_agent_and_returns_text():
    session = FakeSession([response(content="hola".encode("utf-8"))])
    client = HttpClient("agent-test", rate_limit_seconds=0, session=session)
    assert client.get_text("https://example.test") == "hola"
    assert session.headers["User-Agent"] == "agent-test"


def test_http_client_retries_429_then_succeeds():
    session = FakeSession([response(429), response(200, b"pdf")])
    client = HttpClient("agent-test", max_retries=2, rate_limit_seconds=0, session=session)
    assert client.get_bytes("https://example.test") == b"pdf"
    assert session.calls == 2


def test_http_client_distinguishes_http_errors():
    session = FakeSession([response(403)])
    client = HttpClient("agent-test", max_retries=1, rate_limit_seconds=0, session=session)
    with pytest.raises(HttpClientError) as exc:
        client.get_text("https://example.test")
    assert exc.value.status_code == 403


def test_http_client_wraps_request_exception():
    session = FakeSession(error=requests.Timeout("slow"))
    client = HttpClient("agent-test", max_retries=1, rate_limit_seconds=0, session=session)
    with pytest.raises(HttpClientError):
        client.get_text("https://example.test")


def test_check_robots_allowed_flags_disallowed_paths():
    result = check_robots_allowed("User-agent: *\nDisallow: /privado\n", ["/privado/x", "/publico"])
    assert result == {"/privado/x": False, "/publico": True}

