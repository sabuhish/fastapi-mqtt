from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi import FastAPI
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from fastapi_mqtt.config import MQQTConfig

mqtt_config = MQQTConfig()

fast_mqtt = FastMQTT(
    config=mqtt_config,
    topic="/TEST/WILL",
    payload="THIS PROCESS DEAD",
    will_delay_interval=2
)


app = FastAPI()
executor = ThreadPoolExecutor()


@app.on_event("startup")
async def startapp():
    await fast_mqtt.connection()

@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    fast_mqtt.client.subscribe("/last-will")
    fast_mqtt.client.subscribe("/#")
    print("Connected: ", client, flags, rc, properties)


@fast_mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Connected: ", client, topic, payload, qos, properties)


@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")

@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("SUBSCRIBED", client, mid, qos, properties)

@app.get("/")
async def home():
    await fast_mqtt.publish("/hello", "salam")