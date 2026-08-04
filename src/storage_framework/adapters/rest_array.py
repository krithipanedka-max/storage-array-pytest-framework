from __future__ import annotations

from typing import Any

import requests

from storage_framework.core.adapter import StorageArrayAdapter


class RestArrayAdapter(StorageArrayAdapter):
    """Template for a real array adapter.

    Implement each method by calling the vendor REST API and translating responses
    into framework model objects. This class intentionally raises
    NotImplementedError so hardware tests cannot accidentally run with incomplete
    behavior.
    """

    def __init__(self, endpoint: str, token: str | None, verify_tls: bool = True, timeout: int = 30) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_tls
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        self.session.headers["Content-Type"] = "application/json"

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self.session.request(method, f"{self.endpoint}/{path.lstrip('/')}", timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def __getattribute__(self, name: str):
        abstract_names = set(StorageArrayAdapter.__abstractmethods__)
        if name in abstract_names and name not in {"_request"}:
            raise NotImplementedError(f"Implement RestArrayAdapter.{name} for your storage vendor")
        return super().__getattribute__(name)
