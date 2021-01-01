from pydantic import  BaseSettings as Settings
from ssl import SSLContext
from typing import Union
from gmqtt.mqtt.constants import MQTTv50
from warnings import warn


class MQTTConfig(Settings):
    '''
    MQTTConfig is main the configuration to be passsed client object.

    host : To connect MQTT broker, defaults to localhost
    port : To connect MQTT broker, defaults to 1883

    ssl : if given and not false, a SSL/TLS transport is created (by default a plain TCP transport is created)
        If ssl is a ssl.SSLContext object, this context is used to create the transport; if ssl is True, a default context returned from ssl.create_default_context() is used.

    keepalive : Maximum period in seconds between communications with the broker.
        If no other messages are being exchanged, this controls the rate at which
        the client will send ping messages to the broker the keepalive timeout value for the client. Defaults to 60 seconds.

    username : username for authentication, defaults to None
    password : password for authentication, defaults to None

    version : MQTT broker version to use, defaults to  MQTTv50.
        According to gmqtt.Client if your broker does not support 5.0 protocol version and responds with proper CONNACK reason code, client will downgrade to 3.1 and reconnect automatically.

    reconnect_retries && reconnect_delay : By default, connected MQTT client will always try to reconnect in case of lost
        connections. Number of reconnect attempts is unlimited.
        If you want to change this behaviour pass reconnect_retries and reconnect_delay with its values.
        For more info: # https://github.com/wialon/gmqtt#reconnects

    # Last three parameters is used after client disconnects abnormally
    param :: will_message_topic : Topic of the payload
    param :: will_message_payload : The payload
    param :: will_delay_interval : Delay interval
    '''
    host: str = "localhost"
    port: int = 1883
    ssl: Union[bool, SSLContext] = False
    keepalive:  int = 60
    username: str = None
    password: str  = None
    version: int = MQTTv50

    reconnect_retries: int  = None
    reconnect_delay: int = None

    will_message_topic: str = None
    will_message_payload: str = None
    will_delay_interval: int = None


class MQQTConfig(MQTTConfig):
    warn("The MQQTConfig class is renamed MQTTConfig", DeprecationWarning, stacklevel=2)
