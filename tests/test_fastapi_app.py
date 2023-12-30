import asyncio

from async_asgi_testclient import TestClient


async def test_example_app(client: TestClient):
    response = await client.post("/test-publish")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Published"}

    # wait a bit for the published messages to be received and processed
    await asyncio.sleep(0.05)

    # check status of received and processed msgs
    response = await client.get("/test-status")
    assert response.status_code == 200
    assert response.json() == {
        "received_msgs": {"mqtt": 1, "mqtt/test/humidity": 1, "mqtt/test/temperature": 1},
        "processed_msgs": {"mqtt/test/temperature": 1, "mqtt/test/humidity": 2},
        "num_subscriptions": 2,
    }

    response = await client.post("/test-unsubscribe")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Unsubscribed"}

    await asyncio.sleep(0.025)

    response = await client.post("/test-publish")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Published"}

    await asyncio.sleep(0.05)

    response = await client.get("/test-status")
    assert response.status_code == 200
    assert response.json() == {
        "received_msgs": {"mqtt": 1, "mqtt/test/humidity": 2, "mqtt/test/temperature": 1},
        "processed_msgs": {"mqtt/test/temperature": 1, "mqtt/test/humidity": 4},
        "num_subscriptions": 1,
    }

    response = await client.post("/test-reset")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Cleaned"}

    await asyncio.sleep(0.05)

    response = await client.get("/test-status")
    assert response.status_code == 200
    assert response.json() == {
        "received_msgs": {"mqtt": 1, "mqtt/test/humidity": 3, "mqtt/test/temperature": 1},
        "processed_msgs": {"mqtt/test/temperature": 1, "mqtt/test/humidity": 6},
        "num_subscriptions": 1,
    }
