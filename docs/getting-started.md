### 🕹 Guide

After installing the module you setup your `FastApi` app:

The main classes are `FastMQTT` and `MQTTConfig`

```python
from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig

app = FastAPI()

mqtt_config = MQTTConfig()

mqtt = FastMQTT(
    config=mqtt_config
)

```

### `MQTTConfig` class

the class has the following attributes

- host: To connect MQTT broker, defaults to localhost
- port: To connect MQTT broker, defaults to 1883

- ssl: an SSL/TLS transport is created (by default a plain TCP transport is created)
  In case of an ssl.SSLContext object, context is used to create the transport.
  Alternately passing bool value, will set a default context,
  which is calls ssl.create_default_context().

- keepalive: Maximum period in seconds between communications with the broker.
  This controls the rate at which the client will send ping messages.
  Defaults to 60 seconds.

- username: username for authentication, defaults to None
- password: password for authentication, defaults to None

- version: MQTT broker version to use, defaults to MQTTv50.
  According to gmqtt.Client if the broker does not support 5.0 protocol version,
  responds with proper CONNACK reason code,
  the client will downgrade to 3.1 and reconnect automatically.

- reconnect_retries && reconnect_delay: Connected MQTT client always tries to reconnect,
  in case of lost connections. The number of reconnect attempts is unlimited.
  For changing this behavior give reconnect_retries and reconnect_delay values.
  For more info: # https://github.com/wialon/gmqtt#reconnects

The last three parameters are used after the client disconnects abnormally

- will_message_topic: Topic of the payload
- will_message_payload: The payload
- will_delay_interval: Delay interval

### `FastMQTT` client

сlient sets connection parameters before connecting and manipulating the MQTT service.
The object holds session information necessary to connect the MQTT broker.

### `FastMQTT` params

client has the following parameters. The class object holds session information necessary to connect the MQTT broker.

- config: MQTTConfig config object

- client_id: Should be a unique identifier for connection to the MQTT broker.

- clean_session: Enables broker to establish a persistent session.
  In a persistent session clean_session = False.
  The broker stores all subscriptions for the client.
  If the session is not persistent (clean_session = True).
  The broker does not store anything for the client and \
   purges all information from any previous persistent session.
  The client_id identifies the session.

- optimistic_acknowledgement
