from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT


def test_on_connect_runs_when_registered_before_connack():
    mqtt = FastMQTT(config=MQTTConfig())
    calls = []

    @mqtt.on_connect()
    def _connect(client, flags, rc, properties):
        calls.append((client, flags, rc, properties))

    mqtt._FastMQTT__on_connect(mqtt.client, 0, 0, {"session_present": 0})

    assert len(calls) == 1
    assert calls[0][0] is mqtt.client
    assert calls[0][1:] == (0, 0, {"session_present": 0})


def test_on_connect_replays_connack_when_registered_late():
    mqtt = FastMQTT(config=MQTTConfig())
    calls = []

    mqtt._FastMQTT__on_connect(mqtt.client, 1, 0, {"session_present": 1})

    @mqtt.on_connect()
    def _connect(client, flags, rc, properties):
        calls.append((client, flags, rc, properties))

    assert len(calls) == 1
    assert calls[0][0] is mqtt.client
    assert calls[0][1:] == (1, 0, {"session_present": 1})


def test_on_connect_registered_before_connack_is_not_double_called():
    mqtt = FastMQTT(config=MQTTConfig())
    calls = []

    @mqtt.on_connect()
    def _connect(client, flags, rc, properties):
        calls.append(1)

    mqtt._FastMQTT__on_connect(mqtt.client, 0, 0, {})

    assert calls == [1]
