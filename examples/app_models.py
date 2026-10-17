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
