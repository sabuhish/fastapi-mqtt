import asyncio
import contextlib
from typing import Any

from async_asgi_testclient import TestClient

STATUS_TIMEOUT = 5.0


async def _get_status(client: TestClient) -> dict[str, Any]:
    response = await client.get("/test-status")
    assert response.status_code == 200
    return response.json()


async def _wait_for_status(client: TestClient, expected: dict[str, Any]) -> dict[str, Any]:
    """Poll the app status until it matches the expected one, or STATUS_TIMEOUT is reached."""
    status = await _get_status(client)
    with contextlib.suppress(TimeoutError):
        async with asyncio.timeout(STATUS_TIMEOUT):
            while status != expected:
                await asyncio.sleep(0.05)
                status = await _get_status(client)
    return status


async def test_example_app(app_client: TestClient):
    response = await app_client.post("/test-publish")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Published"}

    # wait for the published messages to be received and processed
    expected = {
        "received_msgs": {"fastapi-mqtt": 1, "mqtt/test/humidity": 1, "mqtt/test/temperature": 1},
        "processed_msgs": {"mqtt/test/temperature": 1, "mqtt/test/humidity": 2},
        "num_subscriptions": 2,
    }
    assert await _wait_for_status(app_client, expected) == expected

    response = await app_client.post("/test-unsubscribe")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Unsubscribed"}

    await asyncio.sleep(0.1)

    response = await app_client.post("/test-publish")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Published"}

    expected = {
        "received_msgs": {"fastapi-mqtt": 1, "mqtt/test/humidity": 2, "mqtt/test/temperature": 1},
        "processed_msgs": {"mqtt/test/temperature": 1, "mqtt/test/humidity": 4},
        "num_subscriptions": 1,
    }
    assert await _wait_for_status(app_client, expected) == expected

    response = await app_client.post("/test-reset")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Cleaned"}

    expected = {
        "received_msgs": {"fastapi-mqtt": 1, "mqtt/test/humidity": 3, "mqtt/test/temperature": 1},
        "processed_msgs": {"mqtt/test/temperature": 1, "mqtt/test/humidity": 6},
        "num_subscriptions": 1,
    }
    assert await _wait_for_status(app_client, expected) == expected
