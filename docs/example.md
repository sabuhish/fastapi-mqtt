### Full example

```python

from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi import FastAPI
from fastapi_mqtt.config import MQTTConfig

app = FastAPI()

mqtt_config = MQTTConfig()

fast_mqtt = FastMQTT(config=mqtt_config)

fast_mqtt.init_app(app)

@mqtt.on_connect()
def connect(client, flags, rc, properties):
    mqtt.client.subscribe("/mqtt") #subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Received message: ",topic, payload.decode(), qos, properties)
    return 0

@mqtt.subscribe("my/mqtt/topic/#")
async def message_to_topic(client, topic, payload, qos, properties):
    print("Received message to specific topic: ", topic, payload.decode(), qos, properties)

@mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")

@mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)


@app.get("/")
async def func():
    fast_mqtt.publish("/mqtt", "Hello from Fastapi") #publishing mqtt topic

    return {"result": True,"message":"Published" }
```
