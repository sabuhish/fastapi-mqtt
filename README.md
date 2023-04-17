# fastapi-mqtt

MQTT is a lightweight publish/subscribe messaging protocol designed for M2M (machine to machine) telemetry in low bandwidth environments.
Fastapi-mqtt is the client for working with MQTT.

For more information about MQTT, please refer to here: [MQTT](MQTT.md)

Fatapi-mqtt wraps around [gmqtt](https://github.com/wialon/gmqtt) module. Gmqtt Python async client for MQTT client implementation.
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

- Base Settings available with `pydantic` class
- Authetication to broker with credentials
- unsubscribe certain topics and publish to certain topics

### 🔨 Installation

```sh
 $ pip install fastapi-mqtt
```

### 🕹 Guide

```python
from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig

app = FastAPI()

mqtt_config = MQTTConfig()

mqtt = FastMQTT(
    config=mqtt_config
)

mqtt.init_app(app)



@mqtt.on_connect()
def connect(client, flags, rc, properties):
    mqtt.client.subscribe("/mqtt") #subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Received message: ",topic, payload.decode(), qos, properties)

@mqtt.subscribe("my/mqtt/topic/#")
async def message_to_topic(client, topic, payload, qos, properties):
    print("Received message to specific topic: ", topic, payload.decode(), qos, properties)

@mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")

@mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)

```

Publish method:

```python
async def func():
    mqtt.publish("/mqtt", "Hello from Fastapi") #publishing mqtt topic

    return {"result": True,"message":"Published" }


```

Subscribe method:

```python

@mqtt.on_connect()
def connect(client, flags, rc, properties):
    mqtt.client.subscribe("/mqtt") #subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

```

Changing connection params

```python
mqtt_config = MQTTConfig(host = "mqtt.mosquito.org",
    port= 1883,
    keepalive = 60,
    username="username",
    password="strong_password")


mqtt = FastMQTT(
    config=mqtt_config)

```

# Contributing

Fell free to open issue and send pull request.

Thanks To [Contributors](https://github.com/sabuhish/fastapi-mqtt/graphs/contributors).
Contributions of any kind are welcome!

Before you start please read [CONTRIBUTING](https://github.com/sabuhish/fastapi-mqtt/blob/master/CONTRIBUTING.md)
