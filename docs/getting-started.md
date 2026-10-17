### 🕹 Guide

After installing the module you set up your `FastApi` app.

The main classes are `FastMQTT` and `MQTTConfig`. The client connects to the broker
in the app lifespan:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig()

mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await mqtt.mqtt_startup()
    yield
    await mqtt.mqtt_shutdown()


app = FastAPI(lifespan=_lifespan)
```

The decorated handlers (`@mqtt.on_connect()`, `@mqtt.subscribe(...)`, etc.) are usually
registered at module level. Handlers registered after `mqtt_startup()` also work:
topics are subscribed right away, and `on_connect` handlers are called right away
with the current connection.

`mqtt_shutdown()` accepts an optional MQTT 5.0 DISCONNECT reason code and properties.
For example, reason code 4 (disconnect with will message) asks the broker to publish
the will message:

```python
await mqtt.mqtt_shutdown(reason_code=4, reason_string="shutting down")
```

### `MQTTConfig` class

The class has the following attributes:

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

- reconnect_retries: Number of failed reconnect attempts allowed after a lost connection,
  before giving up (gmqtt makes one more attempt than this number).
  Defaults to -1, which means unlimited attempts.
- reconnect_delay: Delay in seconds between reconnect attempts, defaults to 6.
  For more info: [gmqtt reconnects](https://github.com/wialon/gmqtt#reconnects)

The last three parameters are used after the client disconnects abnormally

- will_message_topic: Topic of the payload
- will_message_payload: The payload
- will_delay_interval: Delay interval

### `FastMQTT` client

The client sets connection parameters before connecting and manipulating the MQTT service.
The object holds session information necessary to connect the MQTT broker.

### `FastMQTT` params

The client has the following parameters:

- config: MQTTConfig config object

- client_id: Should be a unique identifier for connection to the MQTT broker.

- clean_session: Enables broker to establish a persistent session.
  In a persistent session clean_session = False.
  The broker stores all subscriptions for the client.
  If the session is not persistent (clean_session = True).
  The broker does not store anything for the client and
  purges all information from any previous persistent session.
  The client_id identifies the session.

- optimistic_acknowledgement: If True (default), QoS 1/2 messages are acknowledged
  before the message handlers run. If False, they are acknowledged after the handlers finish.
  Only applies to MQTT 5.0.

- mqtt_logger: Optional `logging.Logger` to use.
