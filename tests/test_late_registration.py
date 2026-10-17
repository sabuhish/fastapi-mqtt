"""Handlers and topics registered after the client is connected (issue #98)."""

import asyncio
import uuid
from typing import Any

import pytest
from gmqtt import Client as MQTTClient

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

from .conftest import TEST_BROKER_HOST, TEST_BROKER_PWD, TEST_BROKER_USER


class FakeConnection:
    """Fake connection state for FastMQTT, recording the topics sent to the broker."""

    def __init__(self, mqtt: FastMQTT, monkeypatch: pytest.MonkeyPatch):
        self.mqtt = mqtt
        self.connected = False
        self.subscribed: list[str] = []
        monkeypatch.setattr(MQTTClient, "is_connected", property(lambda _client: self.connected))
        monkeypatch.setattr(
            mqtt.client, "subscribe", lambda sub, **_kw: self.subscribed.append(sub.topic)
        )

    def connack(self, flags: int = 0, rc: int = 0, properties: Any = None) -> None:
        self.connected = True
        # same call gmqtt makes on a successful CONNACK
        self.mqtt.client.on_connect(flags, rc, properties)

    def disconnect(self) -> None:
        self.connected = False


@pytest.fixture
def mqtt() -> FastMQTT:
    return FastMQTT(config=MQTTConfig())


@pytest.fixture
def conn(mqtt: FastMQTT, monkeypatch: pytest.MonkeyPatch) -> FakeConnection:
    return FakeConnection(mqtt, monkeypatch)


async def _noop(*_args):
    return 0


def test_on_connect_registered_before_connack_runs_once(mqtt, conn):
    calls = []
    mqtt.on_connect()(lambda *args: calls.append(args))

    conn.connack(0, 0, {"session_present": 0})

    assert calls == [(mqtt.client, 0, 0, {"session_present": 0})]


def test_on_connect_registered_while_connected_is_called_with_current_connack(mqtt, conn):
    conn.connack(1, 0, {"session_present": 1})
    calls = []

    mqtt.on_connect()(lambda *args: calls.append(args))

    assert calls == [(mqtt.client, 1, 0, {"session_present": 1})]


def test_on_connect_registered_while_disconnected_waits_for_reconnect(mqtt, conn):
    conn.connack(0, 0, None)
    conn.disconnect()
    calls = []

    mqtt.on_connect()(lambda *args: calls.append(args))
    assert calls == []

    conn.connack(1, 0, None)
    assert calls == [(mqtt.client, 1, 0, None)]


def test_subscribe_registered_before_connack_subscribes_on_connect(mqtt, conn):
    mqtt.subscribe("a/b")(_noop)
    assert conn.subscribed == []

    conn.connack()
    assert conn.subscribed == ["a/b"]


def test_subscribe_registered_while_connected_subscribes_now_and_on_reconnect(mqtt, conn):
    conn.connack()
    mqtt.subscribe("a/b")(_noop)
    assert conn.subscribed == ["a/b"]

    conn.disconnect()
    conn.connack()
    assert conn.subscribed == ["a/b", "a/b"]


def test_subscribe_registered_while_disconnected_waits_for_reconnect(mqtt, conn):
    conn.connack()
    conn.disconnect()

    mqtt.subscribe("a/b")(_noop)
    assert conn.subscribed == []

    conn.connack()
    assert conn.subscribed == ["a/b"]


def test_subscribe_from_on_connect_handler_is_sent_once(mqtt, conn):
    @mqtt.on_connect()
    def _connect(client, flags, rc, properties):
        mqtt.subscribe("from/handler")(_noop)

    conn.connack()

    assert conn.subscribed == ["from/handler"]


async def test_late_registration_with_broker():
    """Register `on_connect` and `subscribe` handlers after connecting to a real broker."""
    mqtt = FastMQTT(
        config=MQTTConfig(
            host=TEST_BROKER_HOST, username=TEST_BROKER_USER, password=TEST_BROKER_PWD
        )
    )
    topic = f"fastapi-mqtt/late/{uuid.uuid4().hex}"
    connects = []
    received = asyncio.Event()

    await mqtt.mqtt_startup()
    try:

        @mqtt.on_connect()
        def _connect(client, flags, rc, properties):
            connects.append(rc)

        @mqtt.subscribe(topic, qos=1)
        async def _message(client, msg_topic, payload, qos, properties):
            received.set()

        assert connects == [0]

        await asyncio.sleep(0.2)  # let the SUBSCRIBE reach the broker before publishing
        mqtt.publish(topic, "hello", qos=1)
        await asyncio.wait_for(received.wait(), timeout=5)
    finally:
        await mqtt.mqtt_shutdown()
