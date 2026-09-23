from pathlib import Path
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
        timeout: float | None = None,
    ) -> object | None:
        try:
            response = self._client.request(
                method,
                path,
                json=None if payload is None or files is not None else jsonable_encoder(payload),
                params={key: value for key, value in (params or {}).items() if value is not None},
                files=files,
                timeout=self._client.timeout if timeout is None else timeout,
            )
        except httpx.TimeoutException as error:
            raise ApiError(408, "The server did not respond in time. Please try again.") from error
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
        try:
            response = self._client.get(path)
        except httpx.TimeoutException as error:
            raise ApiError(408, "The server did not respond in time. Please try again.") from error
        if response.is_error:
            raise ApiError(response.status_code, response.text or "Asset download failed")
        return response.content

    def download(self, path: str, destination: Path) -> None:
        try:
            with self._client.stream("GET", path, timeout=120.0) as response:
                self._raise_for_error(response)
                with destination.open("wb") as output:
                    for chunk in response.iter_bytes():
                        output.write(chunk)
        except httpx.TimeoutException as error:
            raise ApiError(408, "The server did not respond in time. Please try again.") from error

    def upload(self, path: str, source: Path, model_type: Any):
        with source.open("rb") as stream:
            return self.model(
                model_type,
                "POST",
                path,
                files={"archive": (source.name, stream)},
                timeout=120.0,
            )

    @staticmethod
    def _raise_for_error(response: httpx.Response) -> None:
        if response.is_error:
            try:
                message = str(response.json().get("detail", response.text))
            except (ValueError, AttributeError):
                message = response.text or f"API request failed with status {response.status_code}"
            raise ApiError(response.status_code, message)

    def model(self, model_type: Any, method: str, path: str, **kwargs: object):
        payload = self.request(method, path, **kwargs)
        return TypeAdapter(model_type).validate_python(payload)
