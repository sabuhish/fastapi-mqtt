"""Disconnect reason code on shutdown (issue #95)."""

import asyncio
import contextlib
import uuid
from typing import Any

import pytest
from gmqtt import Client as MQTTClient

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

from .conftest import TEST_BROKER_HOST, TEST_BROKER_PWD, TEST_BROKER_USER

DISCONNECT_WITH_WILL_MESSAGE = 4


@pytest.fixture
def disconnect_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Any, ...]]:
    calls: list[tuple[Any, ...]] = []

    async def _disconnect(_client, reason_code=0, **properties):
        calls.append((reason_code, properties))

    monkeypatch.setattr(MQTTClient, "disconnect", _disconnect)
    return calls


async def test_shutdown_default_reason_code(disconnect_calls):
    await FastMQTT(config=MQTTConfig()).mqtt_shutdown()

    assert disconnect_calls == [(0, {})]


async def test_shutdown_passes_reason_code_and_properties(disconnect_calls):
    await FastMQTT(config=MQTTConfig()).mqtt_shutdown(
        DISCONNECT_WITH_WILL_MESSAGE, reason_string="shutting down"
    )

    assert disconnect_calls == [(DISCONNECT_WITH_WILL_MESSAGE, {"reason_string": "shutting down"})]


@pytest.mark.parametrize(
    ("reason_code", "will_published"), [(0, False), (DISCONNECT_WITH_WILL_MESSAGE, True)]
)
async def test_shutdown_reason_code_with_broker(reason_code: int, will_published: bool):
    """The broker publishes the will message only for reason code 4."""
    will_topic = f"fastapi-mqtt/will/{uuid.uuid4().hex}"
    received = asyncio.Event()

    observer = MQTTClient(uuid.uuid4().hex)
    observer.on_message = lambda *_args: received.set()
    if TEST_BROKER_USER:
        observer.set_auth_credentials(TEST_BROKER_USER, TEST_BROKER_PWD)
    await observer.connect(TEST_BROKER_HOST)
    observer.subscribe(will_topic, qos=1)

    mqtt = FastMQTT(
        config=MQTTConfig(
            host=TEST_BROKER_HOST,
            username=TEST_BROKER_USER,
            password=TEST_BROKER_PWD,
            will_message_topic=will_topic,
            will_message_payload="gone",
            will_delay_interval=1,
        )
    )
    try:
        await mqtt.mqtt_startup()
        await asyncio.sleep(0.2)  # let the observer subscription reach the broker
        await mqtt.mqtt_shutdown(reason_code)

        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(received.wait(), timeout=3 if will_published else 1.5)
        assert received.is_set() is will_published
    finally:
        await observer.disconnect()
