from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterable

import requests

LOGGER = logging.getLogger(__name__)


class HttpClientError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class HttpClient:
    user_agent: str
    timeout_seconds: float = 30
    max_retries: int = 3
    rate_limit_seconds: float = 1.0
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def get_text(self, url: str) -> str:
        response = self._request("GET", url)
        response.encoding = response.encoding or "utf-8"
        return response.text

    def get_bytes(self, url: str) -> bytes:
        return self._request("GET", url).content

    def _request(self, method: str, url: str) -> requests.Response:
        retryable = {429, 500, 502, 503, 504}
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                delay = self.rate_limit_seconds * (2 ** (attempt - 2))
                LOGGER.info("http_backoff", extra={"url": url, "delay": delay, "attempt": attempt})
                time.sleep(delay)
            try:
                assert self.session is not None
                response = self.session.request(method, url, timeout=self.timeout_seconds)
                if response.status_code in retryable and attempt < self.max_retries:
                    continue
                if response.status_code >= 400:
                    raise HttpClientError(
                        f"HTTP {response.status_code} al consultar {url}", response.status_code
                    )
                time.sleep(self.rate_limit_seconds)
                return response
            except requests.RequestException as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
        raise HttpClientError(f"No se pudo consultar {url}: {last_error}") from last_error


def check_robots_allowed(robots_text: str, paths: Iterable[str]) -> dict[str, bool]:
    disallowed: list[str] = []
    for raw_line in robots_text.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("disallow:"):
            disallowed.append(line.split(":", 1)[1].strip())
    result = {}
    for path in paths:
        result[path] = not any(rule and path.startswith(rule) for rule in disallowed)
    return result

