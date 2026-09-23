"""Low-cardinality metrics and an early ASGI request-body limit."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_OPERATIONS = ("process", "health_live", "health_ready", "metrics", "other")
_STATUS_CLASSES = ("2xx", "3xx", "4xx", "5xx")
_LATENCY_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)


def _operation(scope: Scope) -> str:
    path = scope.get("path", "")
    method = scope.get("method", "")
    known = {
        ("POST", "/process"): "process",
        ("GET", "/health/live"): "health_live",
        ("GET", "/health/ready"): "health_ready",
        ("GET", "/metrics"): "metrics",
    }
    return known.get((method, path), "other")


def _status_class(status_code: int) -> str:
    candidate = f"{status_code // 100}xx"
    return candidate if candidate in _STATUS_CLASSES else "5xx"


@dataclass(slots=True)
class _OperationMetrics:
    requests: dict[str, int] = field(
        default_factory=lambda: {status_class: 0 for status_class in _STATUS_CLASSES}
    )
    errors: dict[str, int] = field(
        default_factory=lambda: {status_class: 0 for status_class in ("4xx", "5xx")}
    )
    latency_count: int = 0
    latency_sum: float = 0.0
    latency_buckets: list[int] = field(default_factory=lambda: [0 for _ in _LATENCY_BUCKETS])
    in_flight: int = 0


class MetricsRegistry:
    """Small in-process Prometheus registry with a fixed label vocabulary."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._operations = {name: _OperationMetrics() for name in _OPERATIONS}
        self._processed_characters = 0
        self._processed_tokens = 0

    def start(self, operation: str) -> None:
        safe_operation = operation if operation in self._operations else "other"
        with self._lock:
            self._operations[safe_operation].in_flight += 1

    def add_processed_characters(self, count: int) -> None:
        with self._lock:
            self._processed_characters += count

    def add_processed_tokens(self, count: int) -> None:
        with self._lock:
            self._processed_tokens += count

    def observe(self, operation: str, status_code: int, elapsed_seconds: float) -> None:
        safe_operation = operation if operation in self._operations else "other"
        status_class = _status_class(status_code)
        with self._lock:
            item = self._operations[safe_operation]
            item.in_flight = max(0, item.in_flight - 1)
            item.requests[status_class] += 1
            if status_class in item.errors:
                item.errors[status_class] += 1
            item.latency_count += 1
            item.latency_sum += elapsed_seconds
            for index, boundary in enumerate(_LATENCY_BUCKETS):
                if elapsed_seconds <= boundary:
                    item.latency_buckets[index] += 1

    def render(self) -> str:
        lines = [
            "# HELP pii_api_requests_total Completed HTTP requests.",
            "# TYPE pii_api_requests_total counter",
        ]
        with self._lock:
            for operation, item in self._operations.items():
                for status_class, value in item.requests.items():
                    lines.append(
                        f'pii_api_requests_total{{operation="{operation}",'
                        f'status_class="{status_class}"}} {value}'
                    )
            lines.extend(
                [
                    "# HELP pii_api_request_errors_total Completed 4xx and 5xx requests.",
                    "# TYPE pii_api_request_errors_total counter",
                ]
            )
            for operation, item in self._operations.items():
                for status_class, value in item.errors.items():
                    lines.append(
                        f'pii_api_request_errors_total{{operation="{operation}",'
                        f'status_class="{status_class}"}} {value}'
                    )
            lines.extend(
                [
                    "# HELP pii_api_request_duration_seconds Request latency.",
                    "# TYPE pii_api_request_duration_seconds histogram",
                ]
            )
            for operation, item in self._operations.items():
                for boundary, value in zip(_LATENCY_BUCKETS, item.latency_buckets, strict=True):
                    lines.append(
                        f'pii_api_request_duration_seconds_bucket{{operation="{operation}",'
                        f'le="{boundary}"}} {value}'
                    )
                lines.append(
                    f'pii_api_request_duration_seconds_bucket{{operation="{operation}",'
                    f'le="+Inf"}} {item.latency_count}'
                )
                lines.append(
                    f'pii_api_request_duration_seconds_sum{{operation="{operation}"}} '
                    f"{item.latency_sum:.9f}"
                )
                lines.append(
                    f'pii_api_request_duration_seconds_count{{operation="{operation}"}} '
                    f"{item.latency_count}"
                )
            lines.extend(
                [
                    "# HELP pii_api_requests_in_flight Currently active HTTP requests.",
                    "# TYPE pii_api_requests_in_flight gauge",
                ]
            )
            for operation, item in self._operations.items():
                lines.append(
                    f'pii_api_requests_in_flight{{operation="{operation}"}} {item.in_flight}'
                )
            lines.extend(
                [
                    "# HELP pii_api_processed_characters_total "
                    "Input characters accepted by /process.",
                    "# TYPE pii_api_processed_characters_total counter",
                    f"pii_api_processed_characters_total {self._processed_characters}",
                    "# HELP pii_api_processed_tokens_total Whitespace-delimited input tokens.",
                    "# TYPE pii_api_processed_tokens_total counter",
                    f'pii_api_processed_tokens_total{{tokenizer="whitespace"}} '
                    f"{self._processed_tokens}",
                ]
            )
        return "\n".join(lines) + "\n"


class RequestMetricsMiddleware:
    """Observe status and latency without recording request data or identifiers."""

    def __init__(self, app: ASGIApp, *, registry: MetricsRegistry) -> None:
        self._app = app
        self._registry = registry

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        operation = _operation(scope)
        started = time.perf_counter()
        status_code = 500
        self._registry.start(operation)

        async def observe_send(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
            await send(message)

        try:
            await self._app(scope, receive, observe_send)
        finally:
            self._registry.observe(operation, status_code, time.perf_counter() - started)


class RequestBodyLimitMiddleware:
    """Reject oversized /process bodies before FastAPI parses JSON."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    @staticmethod
    async def _reject(send: Send, status_code: int, detail: str) -> None:
        body = json.dumps({"detail": detail}, separators=(",", ":")).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not (
            scope["type"] == "http"
            and scope.get("method") == "POST"
            and scope.get("path") == "/process"
        ):
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        declared_length = headers.get(b"content-length")
        if declared_length is not None:
            try:
                parsed_length = int(declared_length)
            except ValueError:
                await self._reject(send, 400, "invalid Content-Length")
                return
            if parsed_length < 0:
                await self._reject(send, 400, "invalid Content-Length")
                return
            if parsed_length > self._max_bytes:
                await self._reject(send, 413, "request body is too large")
                return

        messages: list[Message] = []
        observed_bytes = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            observed_bytes += len(message.get("body", b""))
            if observed_bytes > self._max_bytes:
                await self._reject(send, 413, "request body is too large")
                return
            if not message.get("more_body", False):
                break

        async def replay() -> Message:
            if messages:
                return messages.pop(0)
            return {"type": "http.request", "body": b"", "more_body": False}

        await self._app(scope, replay, send)


AppFactory = Callable[[Scope, Receive, Send], Awaitable[Any]]
