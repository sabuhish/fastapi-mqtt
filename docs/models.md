### Pydantic Models

Message payloads can be typed with pydantic models, both to receive and to publish them.

### Receiving

A subscription handler gets the payload parsed into a pydantic model,
by typing one of its parameters with the model. The parameter name doesn't matter.

```python
from pydantic import BaseModel


class Temperature(BaseModel):
    sensor: str
    value: float


@mqtt.subscribe("sensors/+/temperature")
async def temperature(item: Temperature):
    print(item.sensor, item.value)
```

The other parameters are then passed by name, so the handler can ask for any of
`client`, `topic`, `payload` (the raw bytes), `qos` and `properties`:

```python
@mqtt.subscribe("sensors/+/temperature")
async def temperature(item: Temperature, topic: str):
    print(topic, item.value)
```

- Handlers without a model parameter get `(client, topic, payload, qos, properties)`, as before.
- One model per message: type the parameter with the model itself. `Item | None`,
  `Optional[Item]` or `list[Item]` are not supported. For a JSON list, use a `RootModel`:
  `class Items(RootModel[list[Item]])`, and read the list from `items.root`.
- A handler with more than one model parameter, a model inside other types, or a parameter
  that is not one of the names above, raises a `TypeError` when it is registered.

### Invalid payloads

Messages with a payload that is not valid JSON for the model are skipped by that handler.
Other handlers of the same topic still get them.
By default they are logged as a warning, with the invalid fields but without their values,
which may hold sensitive data.

To handle them yourself, register a payload error handler. It gets the pydantic
`ValidationError`, and replaces the warning:

```python
from pydantic import ValidationError


@mqtt.on_payload_error()
async def invalid_payload(client, topic: str, payload: bytes, error: ValidationError):
    print("Invalid message on", topic, error.errors())
```

The handler can be `async` or not.

### Publishing

`publish` accepts a pydantic model, and sends it as JSON:

```python
mqtt.publish("sensors/kitchen/temperature", Temperature(sensor="kitchen", value=21.5))
```

To customize the JSON, like with `exclude_none=True`, call `model_dump_json(...)`
yourself and publish the resulting string.

### With FastAPI

The same model can be used for the API and for MQTT:

```python
@app.post("/temperature")
async def send_temperature(item: Temperature):
    mqtt.publish(f"sensors/{item.sensor}/temperature", item)
    return {"result": True}
```
