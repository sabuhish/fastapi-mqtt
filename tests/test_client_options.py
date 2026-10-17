import pytest
from pydantic import ValidationError

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT


@pytest.mark.parametrize("value", [True, False])
def test_client_options_are_passed_to_gmqtt(value: bool):
    mqtt = FastMQTT(MQTTConfig(), clean_session=value, optimistic_acknowledgement=value)

    assert mqtt.client._clean_session is value
    assert mqtt.client._package_handler._optimistic_acknowledgement is value


def test_reconnect_retries_default_is_unlimited():
    assert MQTTConfig().reconnect_retries == -1


@pytest.mark.parametrize(
    "options",
    [
        {"reconnect_retries": None},
        {"reconnect_retries": -2},
        {"reconnect_delay": None},
        {"reconnect_delay": -1},
    ],
)
def test_invalid_reconnect_options_are_rejected(options):
    with pytest.raises(ValidationError):
        MQTTConfig(**options)
