# fastapi-mqtt

MQTT is a lightweight publish/subscribe messaging protocol designed for M2M (machine to machine) telemetry in low bandwidth environments.
Fastapi-mqtt is the client for working with MQTT.

For more information about MQTT, please refer to here: [MQTT](MQTT.md)

Fastapi-mqtt wraps around [gmqtt](https://github.com/wialon/gmqtt) module. Gmqtt Python async client for MQTT client implementation.
Module has support of MQTT version 5.0 protocol

[![MIT licensed](https://img.shields.io/github/license/sabuhish/fastapi-mqtt)](https://raw.githubusercontent.com/sabuhish/fastapi-mqtt/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt/network)
[![GitHub issues](https://img.shields.io/github/issues-raw/sabuhish/fastapi-mqtt)](https://github.com/sabuhish/fastapi-mqtt/issues)
[![Downloads](https://pepy.tech/badge/fastapi-mqtt)](https://pepy.tech/project/fastapi-mqtt)

---

## **Documentation**: [FastApi-MQTT](https://sabuhish.github.io/fastapi-mqtt/)

The key feature are:

MQTT specification avaliable with help decarator methods using callbacks:

- on_connect()
- on_disconnect()
- on_subscribe()
- on_message()
- subscribe(topic)

- MQTT Settings available with `pydantic` class
- Authentication to broker with credentials
- unsubscribe certain topics and publish to certain topics

### 🔨 Installation

```sh
pip install fastapi-mqtt
```

### 🕹 Guide

```python
from typing import Any

from fastapi import FastAPI
from gmqtt import Client as MQTTClient

from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig()

fast_mqtt = FastMQTT(config=mqtt_config)

app = FastAPI()
fast_mqtt.init_app(app)


@fast_mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    client.subscribe("/mqtt")  # subscribing mqtt topic
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
    fast_mqtt.publish("/mqtt", "Hello from Fastapi")  # publishing mqtt topic
    return {"result": True, "message": "Published"}
```

Publish method:

```python
async def func():
    fast_mqtt.publish("/mqtt", "Hello from Fastapi")  # publishing mqtt topic
    return {"result": True, "message": "Published"}
```

Subscribe method:

```python
@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    client.subscribe("/mqtt")  # subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)
```

Changing connection params

```python
mqtt_config = MQTTConfig(
    host="mqtt.mosquito.org",
    port=1883,
    keepalive=60,
    username="username",
    password="strong_password",
)
fast_mqtt = FastMQTT(config=mqtt_config)
```

### ✅ Testing

- Clone the repository and install it with [`poetry`](https://python-poetry.org).
- Run tests with `pytest`, using an external MQTT broker to connect (defaults to 'test.mosquitto.org').
- Explore the fastapi app **examples** and run them with uvicorn

```sh
# (opc) Run a local mosquitto MQTT broker with docker
docker run -d --name mosquitto -p 9001:9001 -p 1883:1883 eclipse-mosquitto:1.6.15
# Set host for test broker when running pytest
TEST_BROKER_HOST=localhost pytest
# Run the example apps against local broker, with uvicorn
TEST_BROKER_HOST=localhost uvicorn examples.app:app --port 8000 --reload
TEST_BROKER_HOST=localhost uvicorn examples.ws_app.app:application --port 8000 --reload
```

# Contributing

Fell free to open issue and send pull request.

Thanks To [Contributors](https://github.com/sabuhish/fastapi-mqtt/graphs/contributors).
Contributions of any kind are welcome!

Before you start please read [CONTRIBUTING](https://github.com/sabuhish/fastapi-mqtt/blob/master/CONTRIBUTING.md)
