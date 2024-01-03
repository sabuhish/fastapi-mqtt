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
