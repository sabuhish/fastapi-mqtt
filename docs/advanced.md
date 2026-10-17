### Advanced

### Connection callbacks

Besides `@mqtt.subscribe(...)`, these decorators give access to the low-level MQTT events:

```python
from typing import Any

from gmqtt import Client as MQTTClient


@mqtt.on_connect()
def connect(client: MQTTClient, flags: int, rc: int, properties: Any):
    print("Connected: ", client, flags, rc, properties)


@mqtt.on_message()
async def message(client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any):
    print("Received message: ", topic, payload.decode(), qos, properties)


@mqtt.on_disconnect()
def disconnect(client: MQTTClient, packet, exc=None):
    print("Disconnected")


@mqtt.on_subscribe()
def subscribe(client: MQTTClient, mid: int, qos: int, properties: Any):
    print("subscribed", client, mid, qos, properties)
```

- `on_connect` runs after every successful (re)connection to the broker.
- `on_message` gets every message the client receives, from all its subscriptions.
  The `@mqtt.subscribe(...)` handlers of the topic run too.
- `on_disconnect` runs when the connection is lost or closed.
- `on_subscribe` runs when the broker confirms a subscription.

Topics can also be subscribed directly with the gmqtt client, for example in `on_connect`
with `client.subscribe("topic")`. Their messages only reach `on_message`.

### Registering handlers after startup

Handlers are usually registered at module level, before `mqtt_startup()`.
Handlers registered later also work: topics are subscribed right away,
and `on_connect` handlers are called right away with the current connection.

### Unsubscribe

```python
mqtt.unsubscribe("sensors/+/temperature")
```

The topic is unsubscribed from the broker, and its handlers are removed.

### Shutdown reason code

`mqtt_shutdown()` accepts an optional MQTT 5.0 DISCONNECT reason code and properties:

```python
await mqtt.mqtt_shutdown(reason_code=4, reason_string="shutting down")
```

### Will message

The will message is a message the broker publishes for the client
if it disconnects abnormally, like when the app crashes or loses its network.
It's set up in the config, and sent to the broker when connecting:

```python
mqtt_config = MQTTConfig(
    will_message_topic="status/my-app",
    will_message_payload="offline",
    will_delay_interval=2,
)
```

On a normal shutdown the will message is not published. To publish it anyway,
shut down with reason code 4 (disconnect with will message):

```python
await mqtt.mqtt_shutdown(reason_code=4)
```
