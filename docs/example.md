### Full example

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

fast_mqtt = FastMQTT(config=MQTTConfig())


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()


app = FastAPI(lifespan=_lifespan)


@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    fast_mqtt.client.subscribe("mqtt")  # subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)


@fast_mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Received message: ", topic, payload.decode(), qos, properties)
    return 0


@fast_mqtt.subscribe("my/mqtt/topic/#")
async def message_to_topic(client, topic, payload, qos, properties):
    print("Received message to specific topic: ", topic, payload.decode(), qos, properties)


@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")


@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)


@app.get("/")
async def func():
    fast_mqtt.publish("mqtt", "Hello from Fastapi")  # publishing mqtt topic

    return {"result": True, "message": "Published"}
```

### More complex examples

Visit the [examples](https://github.com/sabuhish/fastapi-mqtt/tree/master/examples) folder for more code examples,
including a full fastAPI app organized in multiple files (splitting dependencies, routes, app creation) implementing a **dynamic MQTT client** through a WebSocket connection.
