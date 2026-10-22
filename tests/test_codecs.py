import logging
import sys
import types
from datetime import datetime, timezone
from typing import Any

import bson
import msgpack
import pytest
from pydantic import BaseModel, RootModel, ValidationError

from fastapi_mqtt.codecs import BSONCodec, JSONCodec, MsgPackCodec
from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT


class MyItem(BaseModel):
    value: int


async def _deliver(mqtt: FastMQTT, topic: str, payload: bytes):
    """Deliver a message to the handlers, as gmqtt does when it arrives."""
    return await mqtt.client.on_message(topic, payload, 0, {})


def _capture_publish(mqtt: FastMQTT, monkeypatch: pytest.monkeypatch) -> list[Any]:
    sent: list[Any] = []
    monkeypatch.setattr(
        mqtt.client, "publish", lambda topic, payload=None, **kwargs: sent.append(payload)
    )
    return sent


def test_default_codec_is_json():
    assert isinstance(FastMQTT(config=MQTTConfig()).codec, JSONCodec)


@pytest.mark.parametrize("codec", [JSONCodec(), MsgPackCodec(), BSONCodec()])
def test_round_trip(codec):
    assert codec.decode(MyItem, codec.encode(MyItem(value=3))) == MyItem(value=3)


async def test_global_codec_for_subscribe_and_publish(monkeypatch):
    mqtt = FastMQTT(config=MQTTConfig(), codec=MsgPackCodec())
    received = []

    @mqtt.subscribe("topic")
    async def handler(item: MyItem):
        received.append(item)

    await _deliver(mqtt, "topic", msgpack.packb({"value": 3}))
    sent = _capture_publish(mqtt, monkeypatch)
    mqtt.publish("topic", MyItem(value=4))
    mqtt.publish("topic", "raw text")

    assert received == [MyItem(value=3)]
    assert sent == [msgpack.packb({"value": 4}), "raw text"]


async def test_subscription_codec_overrides_global():
    mqtt = FastMQTT(config=MQTTConfig())
    received = []

    @mqtt.subscribe("topic", codec=MsgPackCodec())
    async def packed(item: MyItem):
        received.append(("msgpack", item))

    @mqtt.subscribe("other")
    async def json(item: MyItem):
        received.append(("json", item))

    await _deliver(mqtt, "topic", msgpack.packb({"value": 1}))
    await _deliver(mqtt, "other", b'{"value": 2}')

    assert received == [("msgpack", MyItem(value=1)), ("json", MyItem(value=2))]


def test_publish_codec_override(monkeypatch):
    mqtt = FastMQTT(config=MQTTConfig())
    sent = _capture_publish(mqtt, monkeypatch)

    mqtt.publish("topic", MyItem(value=5), codec=MsgPackCodec())

    assert sent == [msgpack.packb({"value": 5})]


async def test_msgpack_list_with_root_model():
    class Items(RootModel[list[MyItem]]):
        pass

    mqtt = FastMQTT(config=MQTTConfig(), codec=MsgPackCodec())
    received = []

    @mqtt.subscribe("topic")
    async def handler(items: Items):
        received.append(items.root)

    await _deliver(mqtt, "topic", msgpack.packb([{"value": 1}, {"value": 2}]))

    assert received == [[MyItem(value=1), MyItem(value=2)]]


@pytest.mark.parametrize("payload", [b"\xc1", b"", b'{"value":1}'])
async def test_undecodable_payload_goes_to_payload_error(payload):
    mqtt = FastMQTT(config=MQTTConfig(), codec=MsgPackCodec())
    errors = []

    @mqtt.on_payload_error()
    def on_error(client, topic, payload, error):
        errors.append(error)

    @mqtt.subscribe("topic")
    async def handler(item: MyItem): ...

    await _deliver(mqtt, "topic", payload)

    assert len(errors) == 1
    assert isinstance(errors[0], ValidationError)


async def test_decode_error_log_has_no_input_values(caplog):
    mqtt = FastMQTT(config=MQTTConfig(), codec=MsgPackCodec())

    @mqtt.subscribe("topic")
    async def handler(item: MyItem): ...

    with caplog.at_level(logging.WARNING):
        await _deliver(mqtt, "topic", b"secret-value")

    assert "Invalid msgpack payload" in caplog.text
    assert "secret-valyue" not in caplog.text


def test_missing_msgpack_has_helpful_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "msgpack", None)
    with pytest.raises(ImportError, match=r"fastapi-mqtt\[msgpack\]"):
        MsgPackCodec()


def test_standalone_bson_package_is_rejected(monkeypatch):
    monkeypatch.setitem(sys.modules, "bson", types.ModuleType("bson"))
    with pytest.raises(ImportError, match="pymongo"):
        BSONCodec()


# bson tests
async def test_bson_codec_for_subscribe_and_publish(monkeypatch):
    mqtt = FastMQTT(config=MQTTConfig(), codec=BSONCodec())
    received = []

    @mqtt.subscribe("topic")
    async def handler(item: MyItem):
        received.append(item)

    await _deliver(mqtt, "topic", bson.encode({"value": 23}))
    sent = _capture_publish(mqtt, monkeypatch)
    mqtt.publish("topic", MyItem(value=32))

    assert received == [MyItem(value=23)]
    assert sent == [bson.encode({"value": 32})]


def test_bson_needs_object_at_top_level():
    class Items(RootModel[list[MyItem]]):
        pass

    with pytest.raises(TypeError):
        BSONCodec().encode(Items([MyItem(value=11)]))


@pytest.mark.parametrize("payload", [b"", b"\x05\x00\x00\x00", b'{"value":1}'])
async def test_invalid_bson_goes_to_payload_error(payload):
    mqtt = FastMQTT(config=MQTTConfig(), codec=BSONCodec())
    errors = []

    @mqtt.on_payload_error()
    def on_error(client, topic, payload, error):
        errors.append(error)

    @mqtt.subscribe("topic")
    async def handler(item: MyItem): ...

    await _deliver(mqtt, "topic", payload)

    assert len(errors) == 1
    assert isinstance(errors[0], ValidationError)


async def test_bson_decode_error_log_has_no_input_values(caplog):
    mqtt = FastMQTT(config=MQTTConfig(), codec=BSONCodec())

    @mqtt.subscribe("topic")
    async def handler(item: MyItem): ...

    with caplog.at_level(logging.WARNING):
        await _deliver(mqtt, "topic", b"secret-value")

    assert "Invalid bson payload" in caplog.text
    assert "secret-value" not in caplog.text


@pytest.mark.parametrize("codec", [MsgPackCodec(), BSONCodec()])
def test_round_trip_with_types_no_native_to_the_format(codec):
    class Event(BaseModel):
        at: datetime
        tags: set[str]

    event = Event(at=datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc), tags={"a"})
    assert codec.decode(Event, codec.encode(event)) == event


def test_missing_pymongo_has_helpful_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "bson", None)
    with pytest.raises(ImportError, match=r"fastapi-mqtt\[bson\]"):
        BSONCodec()


async def test_decode_error_reason_is_never_empty():
    mqtt = FastMQTT(config=MQTTConfig(), codec=MsgPackCodec())
    errors = []

    @mqtt.on_payload_error()
    def on_error(client, topic, payload, error):
        errors.append(error)

    @mqtt.subscribe("topic")
    async def handler(item: MyItem): ...

    await _deliver(mqtt, "topic", b"\xc1")
    assert errors[0].errors()[0]["ctx"]["reason"] != ""
