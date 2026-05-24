"""
HTTP health check using httpx AsyncClient.

One request per endpoint; optional retry for transient network blips.
"""

import asyncio
import time
from dataclasses import dataclass

import httpx

from app.models.endpoint import Endpoint


@dataclass
class HealthCheckResult:
    is_up: bool
    status_code: int | None
    response_time_ms: int | None
    failure_reason: str | None


async def _execute_request(
    client: httpx.AsyncClient,
    endpoint: Endpoint,
) -> HealthCheckResult:
    """Send one HTTP request and compare status code to expected."""
    start = time.perf_counter()

    try:
        response = await client.request(
            method=endpoint.http_method.value,
            url=endpoint.url,
        )
        response_time_ms = int((time.perf_counter() - start) * 1000)
        is_up = response.status_code == endpoint.expected_status_code

        failure_reason = None
        if not is_up:
            failure_reason = (
                f"Expected status {endpoint.expected_status_code}, "
                f"got {response.status_code}"
            )

        return HealthCheckResult(
            is_up=is_up,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            failure_reason=failure_reason,
        )

    except httpx.TimeoutException:
        elapsed = int((time.perf_counter() - start) * 1000)
        return HealthCheckResult(
            is_up=False,
            status_code=None,
            response_time_ms=elapsed,
            failure_reason="Request timed out",
        )
    except httpx.RequestError as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return HealthCheckResult(
            is_up=False,
            status_code=None,
            response_time_ms=elapsed,
            failure_reason=str(exc),
        )


async def perform_health_check(
    endpoint: Endpoint,
    timeout_seconds: float = 30.0,
    max_retries: int = 1,
) -> HealthCheckResult:
    """
    Check an endpoint with httpx.

    POST/PUT/PATCH/DELETE are sent without a body (uptime check only).
  """
    # HEAD is valid for uptime; other write methods use empty body
    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=True,
    ) as client:
        last_result: HealthCheckResult | None = None

        for attempt in range(max_retries + 1):
            last_result = await _execute_request(client, endpoint)
            if last_result.is_up:
                return last_result
            if attempt < max_retries:
                await asyncio.sleep(1)

        assert last_result is not None
        return last_result
