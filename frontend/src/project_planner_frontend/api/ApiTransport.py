from typing import Any

import httpx
from fastapi.encoders import jsonable_encoder
from pydantic import TypeAdapter

from project_planner_frontend.api.ApiError import ApiError


class ApiTransport:
    def __init__(
        self,
        base_url: str,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
        api_token: str | None = None,
    ) -> None:
        headers = {"Authorization": f"Bearer {api_token}"} if api_token else None
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            transport=transport,
            headers=headers,
        )

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: object | None = None,
        params: dict[str, object] | None = None,
        files: dict[str, object] | None = None,
    ) -> object | None:
        response = self._client.request(
            method,
            path,
            json=None if payload is None or files is not None else jsonable_encoder(payload),
            params={key: value for key, value in (params or {}).items() if value is not None},
            files=files,
        )
        if response.is_error:
            try:
                message = str(response.json().get("detail", response.text))
            except (ValueError, AttributeError):
                message = response.text or f"API request failed with status {response.status_code}"
            raise ApiError(response.status_code, message)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def request_bytes(self, path: str) -> bytes:
        response = self._client.get(path)
        if response.is_error:
            raise ApiError(response.status_code, response.text or "Asset download failed")
        return response.content

    def model(self, model_type: Any, method: str, path: str, **kwargs: object):
        payload = self.request(method, path, **kwargs)
        return TypeAdapter(model_type).validate_python(payload)
