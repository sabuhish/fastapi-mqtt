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

### Example with pydantic models

The same `Temperature` model is used for the API body, for publishing and for receiving.
Invalid messages go to the `on_payload_error` handler.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, ValidationError

from fastapi_mqtt import FastMQTT, MQTTConfig

mqtt_config = MQTTConfig()

fast_mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    await fast_mqtt.mqtt_startup()
    yield
    await fast_mqtt.mqtt_shutdown()


app = FastAPI(lifespan=_lifespan)


class Temperature(BaseModel):
    sensor: str
    value: float


# last temperature received from each sensor
latest: dict[str, Temperature] = {}


@fast_mqtt.subscribe("sensors/+/temperature", qos=1)
async def temperature(item: Temperature, topic: str):
    """The payload arrives parsed and validated as a Temperature."""
    print("Received temperature: ", topic, item)
    latest[item.sensor] = item


@fast_mqtt.on_payload_error()
async def invalid_payload(client, topic: str, payload: bytes, error: ValidationError):
    """Messages that are not a valid Temperature come here, instead of to the handler."""
    print("Invalid message on", topic, error.errors(include_input=False))


@app.post("/temperature")
async def send_temperature(item: Temperature):
    """The same model is used for the API body and for the MQTT message."""
    fast_mqtt.publish(f"sensors/{item.sensor}/temperature", item, qos=1)
    return {"result": True, "message": "Published"}


@app.get("/temperature")
async def get_temperatures() -> dict[str, Temperature]:
    return latest
```

Run it against a local broker, and publish a temperature through the API:

```sh
uvicorn examples.app_models:app --port 8000
curl -X POST localhost:8000/temperature -H 'content-type: application/json' \
  -d '{"sensor": "kitchen", "value": 21.5}'
curl localhost:8000/temperature
```

### More complex examples

Visit the [examples](https://github.com/sabuhish/fastapi-mqtt/tree/master/examples) folder for more code examples,
including a full fastAPI app organized in multiple files (splitting dependencies, routes, app creation) implementing a **dynamic MQTT client** through a WebSocket connection.
