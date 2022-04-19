from ssl import SSLContext
from typing import Optional, Union

from gmqtt.mqtt.constants import MQTTv50
from pydantic import BaseSettings as Settings


class MQTTConfig(Settings):
    """
    MQTTConfig is main the configuration to be passed client object.

    host: To connect MQTT broker, defaults to localhost
    port: To connect MQTT broker, defaults to 1883

    ssl: an SSL/TLS transport is created (by default a plain TCP transport is created)
        In case of an ssl.SSLContext object, context is used to create the transport.
        Alternately passing bool value, will set  a default context,
        which is calls ssl.create_default_context().

    keepalive: Maximum period in seconds between communications with the broker.
        This controls the rate at which the client will send ping messages.
        Defaults to 60 seconds.

    username: username for authentication, defaults to None
    password: password for authentication, defaults to None

    version: MQTT broker version to use, defaults to  MQTTv50.
        According to gmqtt.Client if the broker does not support 5.0 protocol version,
        responds with proper CONNACK reason code,
        the client will downgrade to 3.1 and reconnect automatically.

    reconnect_retries && reconnect_delay: Connected MQTT client always tries to reconnect,
        in case of lost connections. The number of reconnect attempts is unlimited.
        For changing this behavior give reconnect_retries and reconnect_delay values.
        For more info: # https://github.com/wialon/gmqtt#reconnects

    The last three parameters are used after the client disconnects abnormally

    will_message_topic: Topic of the payload
    will_message_payload: The payload
    will_delay_interval: Delay interval
    """

    host: str = 'localhost'
    port: int = 1883
    ssl: Union[bool, SSLContext] = False
    keepalive: int = 60
    username: Optional[str] = None
    password: Optional[str] = None
    version: int = MQTTv50

    reconnect_retries: Optional[int] = None
    reconnect_delay: Optional[int] = None

    will_message_topic: Optional[str] = None
    will_message_payload: Optional[str] = None
    will_delay_interval: Optional[str] = None
