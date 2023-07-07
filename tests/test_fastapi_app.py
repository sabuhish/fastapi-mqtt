import asyncio

from async_asgi_testclient import TestClient


async def test_example_app(client: TestClient):
    response = await client.post("/test-publish")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Published"}

    # wait a bit for the published messages to be received and processed
    await asyncio.sleep(0.025)

    response = await client.post("/test-unsubscribe")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Unsubscribed"}

    await asyncio.sleep(0.025)

    response = await client.post("/test-reset")
    assert response.status_code == 200
    assert response.json() == {"result": True, "message": "Cleaned"}

    await asyncio.sleep(0.015)
