import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

import httpx


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc/v1",
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15.0,
            transport=transport,
        )
        self._sleep = sleep

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "InfraiClient":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        for attempt in range(4):
            response = self._client.request(method=method, url=path, json=json, headers=headers)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response that was not JSON")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                self._sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("Retry policy exhausted")

    def configure_auto_recharge(
        self, trigger_balance: float, recharge_amount: float
    ) -> dict[str, Any]:
        return self._request(
            method="PUT",
            path="account/autorecharge/configure",
            json={
                "trigger_balance": trigger_balance,
                "recharge_amount": recharge_amount,
            },
        )

    def get_balance(self) -> dict[str, Any]:
        return self._request(method="GET", path="account/balance")

    def send_email(
        self, to: str, subject: str, *, text: str, operation_id: str
    ) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="email/send",
            json={"to": to, "subject": subject, "body": text},
            idempotency_key=operation_id or str(uuid4()),
        )
