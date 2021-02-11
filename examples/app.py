from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi import FastAPI
from fastapi_mqtt.config import MQQTConfig

mqtt_config = MQQTConfig()

fast_mqtt = FastMQTT(
    config=mqtt_config
)


app = FastAPI()

fast_mqtt.init_app(app)


@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    fast_mqtt.client.subscribe("/mqtt") #subscribing mqtt topic 
    print("Connected: ", client, flags, rc, properties)

@fast_mqtt.subscribe("mqtt/+/temperature", "mqtt/+/humidity")
async def home_message(client, topic, payload, qos, properties):
    print("temperature/humidity: ", topic, payload.decode(), qos, properties)
    return 0

@fast_mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Received message: ",topic, payload.decode(), qos, properties)
    return 0

@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")

@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)

@app.get("/")
async def func():
    await fast_mqtt.publish("/mqtt", "Hello from Fastapi") #publishing mqtt topic 

    return {"result": True,"message":"Published" }