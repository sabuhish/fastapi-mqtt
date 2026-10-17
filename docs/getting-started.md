### 🕹 Getting Started

After installing the module you set up your `FastApi` app.

The main classes are `FastMQTT` and `MQTTConfig`. The client connects to the broker
in the app lifespan:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig(host="localhost", port=1883)

mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await mqtt.mqtt_startup()
    yield
    await mqtt.mqtt_shutdown()


app = FastAPI(lifespan=_lifespan)
```

See [Configuration](configuration.md) for all the connection options.

### Subscribe

Decorate a handler with `@mqtt.subscribe(...)` to receive the messages of one or more topics.
Topics can use the MQTT wildcards `+` (one level) and `#` (all levels below):

```python
@mqtt.subscribe("sensors/+/temperature", "sensors/+/humidity", qos=1)
async def sensor_message(client, topic, payload, qos, properties):
    print("Received: ", topic, payload.decode(), qos, properties)
```

The handler gets the client, the topic of the message, the payload as bytes,
the QoS level and the MQTT 5.0 properties.

Subscriptions made with the decorator are renewed automatically when the client reconnects.
Payloads can also be received as pydantic models, see [Pydantic Models](models.md).

### Publish

Publish a message to a topic, for example from a FastAPI endpoint:

```python
@app.post("/hello")
async def hello():
    mqtt.publish("greetings", "Hello from FastAPI")
    return {"result": True, "message": "Published"}
```

`publish` also takes `qos` and `retain` arguments, and accepts pydantic models as payload.

### Next steps

- [Pydantic Models](models.md): receive and publish typed messages
- [Advanced](advanced.md): connection callbacks, unsubscribing, shutdown and will messages
- [Example](example.md): a full app
