# fastapi-mqtt

MQTT is a lightweight publish/subscribe messaging protocol designed for M2M (machine to machine) telemetry in low bandwidth environments.
Fastapi-mqtt is the client for working with MQTT.

For more information about MQTT, please refer to here: [MQTT](https://sabuhish.github.io/fastapi-mqtt/mqtt/)

Fastapi-mqtt wraps around the [gmqtt](https://github.com/wialon/gmqtt) module, a Python async MQTT client.
The module supports the MQTT version 5.0 protocol.

[![MIT licensed](https://img.shields.io/github/license/sabuhish/fastapi-mqtt)](https://raw.githubusercontent.com/sabuhish/fastapi-mqtt/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt/network)
[![GitHub issues](https://img.shields.io/github/issues-raw/sabuhish/fastapi-mqtt)](https://github.com/sabuhish/fastapi-mqtt/issues)
[![Downloads](https://pepy.tech/badge/fastapi-mqtt)](https://pepy.tech/project/fastapi-mqtt)

---

## **Documentation**: [FastApi-MQTT](https://sabuhish.github.io/fastapi-mqtt/)

The key features are:

MQTT specification available with the help of decorator methods using callbacks:

- on_connect()
- on_disconnect()
- on_subscribe()
- on_message()
- subscribe(topic)

- MQTT Settings available with `pydantic` class
- Authentication to broker with credentials
- unsubscribe certain topics and publish to certain topics

### 🔨 Installation

Requires Python 3.12 or newer.

```sh
pip install fastapi-mqtt
```

### 🕹 Guide

```python
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from gmqtt import Client as MQTTClient

from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig()
fast_mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()


app = FastAPI(lifespan=_lifespan)


@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    client.subscribe("mqtt")  # subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)


@fast_mqtt.subscribe("mqtt/+/temperature", "mqtt/+/humidity", qos=1)
async def home_message(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    print("temperature/humidity: ", topic, payload.decode(), qos, properties)


@fast_mqtt.on_message()
async def message(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    print("Received message: ", topic, payload.decode(), qos, properties)


@fast_mqtt.subscribe("my/mqtt/topic/#", qos=2)
async def message_to_topic_with_high_qos(
    client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
):
    print(
        "Received message to specific topic and QoS=2: ", topic, payload.decode(), qos, properties
    )


@fast_mqtt.on_disconnect()
def disconnect(client: MQTTClient, packet, exc=None):
    print("Disconnected")


@fast_mqtt.on_subscribe()
def subscribe(client: MQTTClient, mid: int, qos: int, properties: Any):
    print("subscribed", client, mid, qos, properties)


@app.get("/test")
async def func():
    fast_mqtt.publish("mqtt", "Hello from Fastapi")  # publishing mqtt topic
    return {"result": True, "message": "Published"}
```

Handlers are usually registered at module level, as above. Handlers registered after
`mqtt_startup()` also work: topics are subscribed right away, and `on_connect` handlers
are called right away with the current connection.

Publish method:

```python
async def func():
    fast_mqtt.publish("mqtt", "Hello from Fastapi")  # publishing mqtt topic
    return {"result": True, "message": "Published"}
```

Subscribe method, with a handler for the messages of the topic:

```python
@fast_mqtt.subscribe("mqtt/+/temperature", qos=1)
async def temperature(client, topic, payload, qos, properties):
    print("temperature: ", topic, payload.decode(), qos, properties)
```

Subscriptions made with the decorator are renewed automatically when the client reconnects.

Changing connection params

```python
mqtt_config = MQTTConfig(
    host="test.mosquitto.org",
    port=1883,
    keepalive=60,
    username="username",
    password="strong_password",
)
fast_mqtt = FastMQTT(config=mqtt_config)
```

### ✅ Testing

- Clone the repository and install it with [`poetry`](https://python-poetry.org).
- Run tests with `pytest` against a local MQTT broker, or set `TEST_BROKER_HOST` to use another one.
- Explore the fastapi app **examples** and run them with uvicorn

```sh
# Run a local mosquitto MQTT broker with docker
docker run -d --rm --name mosquitto -p 1883:1883 eclipse-mosquitto:1.6.15
# Run the tests against the local broker
pytest
# Run the example apps against the local broker, with uvicorn
uvicorn examples.app:app --port 8000 --reload
uvicorn examples.ws_app.app:application --port 8000 --reload
```

# Contributing

Feel free to open issues and send pull requests.

Thanks To [Contributors](https://github.com/sabuhish/fastapi-mqtt/graphs/contributors).
Contributions of any kind are welcome!

Before you start please read [CONTRIBUTING](https://github.com/sabuhish/fastapi-mqtt/blob/master/CONTRIBUTING.md)
