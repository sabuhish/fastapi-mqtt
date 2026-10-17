"""Pydantic model payloads for subscription handlers and publish (issue #51)."""

import asyncio
import logging
import uuid
from typing import Optional

import pytest
from pydantic import BaseModel, RootModel, ValidationError

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

from .conftest import TEST_BROKER_HOST, TEST_BROKER_PWD, TEST_BROKER_USER


class MyItem(BaseModel):
    value: int


@pytest.fixture
def mqtt() -> FastMQTT:
    return FastMQTT(config=MQTTConfig())


async def _deliver(mqtt: FastMQTT, topic: str, payload: bytes):
    """Deliver a message to the handlers, as gmqtt does when it arrives."""
    return await mqtt.client.on_message(topic, payload, 0, {})


async def test_handler_with_only_the_model(mqtt):
    received = []

    @mqtt.subscribe("topic")
    async def topic(item: MyItem):
        received.append(item)

    await _deliver(mqtt, "topic", b'{"value": 3}')

    assert received == [MyItem(value=3)]


async def test_handler_with_model_and_message_args_by_name(mqtt):
    received = []

    @mqtt.subscribe("sensors/+/value")
    async def handler(topic: str, item: MyItem, qos: int):
        received.append((topic, item, qos))

    await _deliver(mqtt, "sensors/1/value", b'{"value": 7}')

    assert received == [("sensors/1/value", MyItem(value=7), 0)]


async def test_payload_parameter_typed_as_model(mqtt):
    received = []

    @mqtt.subscribe("topic")
    async def handler(client, topic, payload: MyItem, qos, properties):
        received.append(payload)

    await _deliver(mqtt, "topic", b'{"value": 1}')

    assert received == [MyItem(value=1)]


async def test_json_list_with_root_model(mqtt):
    class Items(RootModel[list[MyItem]]):
        pass

    received = []

    @mqtt.subscribe("topic")
    async def handler(items: Items):
        received.append(items.root)

    await _deliver(mqtt, "topic", b'[{"value": 1}, {"value": 2}]')

    assert received == [[MyItem(value=1), MyItem(value=2)]]


async def test_classic_handler_is_unchanged(mqtt):
    received = []

    async def handler(client, topic, payload: bytes, qos, properties):
        received.append(payload)

    assert mqtt.subscribe("topic")(handler) is handler
    assert mqtt.subscriptions["topic"][1] == [handler]

    await _deliver(mqtt, "topic", b"raw")

    assert received == [b"raw"]


@pytest.mark.parametrize("payload", [b"not json", b'{"value": "abc"}', b""])
async def test_invalid_payload_is_logged_and_skipped(mqtt, caplog, payload):
    received = []
    raw = []

    @mqtt.subscribe("topic")
    async def handler(item: MyItem):
        received.append(item)

    @mqtt.subscribe("topic")
    async def raw_handler(client, topic, payload, qos, properties):
        raw.append(payload)

    with caplog.at_level(logging.WARNING):
        await _deliver(mqtt, "topic", payload)

    assert received == []
    assert raw == [payload]  # other handlers of the topic still run
    assert "Invalid payload on topic topic for handler handler" in caplog.text


async def test_invalid_payload_log_has_no_input_values(mqtt, caplog):
    @mqtt.subscribe("topic")
    async def handler(item: MyItem): ...

    with caplog.at_level(logging.WARNING):
        await _deliver(mqtt, "topic", b'{"value": "secret-value"}')

    assert "value: Input should be a valid integer" in caplog.text
    assert "secret-value" not in caplog.text


@pytest.mark.parametrize("sync", [False, True])
async def test_payload_error_handler(mqtt, caplog, sync):
    errors = []

    if sync:

        @mqtt.on_payload_error()
        def on_error(client, topic, payload, error):
            errors.append((topic, payload, error))

    else:

        @mqtt.on_payload_error()
        async def on_error(client, topic, payload, error):
            errors.append((topic, payload, error))

    received = []

    @mqtt.subscribe("topic")
    async def handler(item: MyItem):
        received.append(item)

    with caplog.at_level(logging.WARNING):
        await _deliver(mqtt, "topic", b'{"value": "abc"}')
        await _deliver(mqtt, "topic", b'{"value": 2}')

    assert received == [MyItem(value=2)]
    assert [(topic, payload) for topic, payload, _ in errors] == [("topic", b'{"value": "abc"}')]
    assert isinstance(errors[0][2], ValidationError)
    assert "Invalid payload" not in caplog.text  # the error handler replaces the warning


def test_more_than_one_model_parameter_is_rejected(mqtt):
    with pytest.raises(TypeError, match="more than one pydantic model"):

        @mqtt.subscribe("topic")
        async def handler(first: MyItem, second: MyItem): ...


@pytest.mark.parametrize("hint", [MyItem | None, Optional[MyItem], list[MyItem]])
def test_model_inside_other_types_is_rejected(mqtt, hint):
    async def handler(item): ...

    handler.__annotations__ = {"item": hint}
    with pytest.raises(TypeError, match="type it with the pydantic model itself"):
        mqtt.subscribe("topic")(handler)


def test_handler_without_model_must_accept_message_args(mqtt):
    with pytest.raises(TypeError, match="must accept the arguments"):

        @mqtt.subscribe("topic")
        async def handler(item): ...


def test_classic_handler_with_unresolvable_hints_is_accepted(mqtt):
    async def handler(client, topic, payload, qos, properties): ...

    handler.__annotations__ = {"client": "NotImported"}
    assert mqtt.subscribe("topic")(handler) is handler


def test_handler_without_readable_signature_is_called_as_usual(mqtt):
    class Handler:
        @property
        def __signature__(self):
            raise ValueError("no signature")

        async def __call__(self, *args): ...

    handler = Handler()
    assert mqtt.subscribe("topic")(handler) is handler


def test_positional_only_model_handler_is_rejected(mqtt):
    with pytest.raises(TypeError, match="can't be called with keyword arguments"):

        @mqtt.subscribe("topic")
        async def handler(item: MyItem, /): ...


def test_unknown_parameter_is_rejected(mqtt):
    with pytest.raises(TypeError, match=r"unknown parameters \['other'\]"):

        @mqtt.subscribe("topic")
        async def handler(item: MyItem, other: str): ...


def test_publish_sends_model_as_json(mqtt, monkeypatch):
    sent = []
    monkeypatch.setattr(
        mqtt.client, "publish", lambda topic, payload=None, **kwargs: sent.append(payload)
    )

    mqtt.publish("topic", MyItem(value=3))
    mqtt.publish("topic", "raw text")

    assert sent == ['{"value":3}', "raw text"]


async def test_payload_model_with_broker():
    """Publish a model to a real broker and receive it as a model."""
    mqtt = FastMQTT(
        config=MQTTConfig(
            host=TEST_BROKER_HOST, username=TEST_BROKER_USER, password=TEST_BROKER_PWD
        )
    )
    topic = f"fastapi-mqtt/models/{uuid.uuid4().hex}"
    received: asyncio.Queue[MyItem] = asyncio.Queue()

    @mqtt.subscribe(topic, qos=1)
    async def handler(item: MyItem):
        await received.put(item)

    await mqtt.mqtt_startup()
    try:
        await asyncio.sleep(0.2)  # let the SUBSCRIBE reach the broker before publishing
        mqtt.publish(topic, MyItem(value=42), qos=1)
        assert await asyncio.wait_for(received.get(), timeout=5) == MyItem(value=42)
    finally:
        await mqtt.mqtt_shutdown()
