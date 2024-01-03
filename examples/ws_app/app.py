import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from uvicorn.config import logger

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

from .mqtt_ws_client import DynamicMQTTClient
from .router import mqtt_router

# NOTE: Need to `pip install websockets` to make it work,
# or a 'No supported WebSocket library detected' warning will appear.

# Run MQTT broker in background for tests with:
# `docker run -d --name mosquitto -p 9001:9001 -p 1883:1883 eclipse-mosquitto:1.6.15`
TEST_BROKER_HOST = os.getenv("TEST_BROKER_HOST", default="localhost")


def create_app():
    """Example fastAPI app with dynamic MQTT client."""
    fast_mqtt = FastMQTT(config=MQTTConfig(host=TEST_BROKER_HOST))

    ws_subscribers = DynamicMQTTClient(fast_mqtt)

    @asynccontextmanager
    async def _lifespan(fastapi_app: FastAPI):
        await fast_mqtt.mqtt_startup()
        fastapi_app.state.ws_subscribers = ws_subscribers
        yield
        await ws_subscribers.close()
        await fast_mqtt.mqtt_shutdown()

    app = FastAPI(lifespan=_lifespan)

    @fast_mqtt.on_message()
    async def _process_message(_client, topic, payload, qos, properties):
        """
        Common method to dispatch all received MQTT messages.

        If there are multiple subscriptions that match the same topic of the
        received message, this method will be called multiple times.

        Example:
             * Client is subscribed to 'test/#' and 'test/hello/+'
             * Broker receives a message with topic 'test/hello/there'
             * This method is called 2 times with the same topic and payload,
               **one for each topic match** in the client subscriptions.
        """
        num_clients_send_to = await ws_subscribers.send_mqtt_msg(fast_mqtt, topic, payload.decode())
        logger.info(
            "Received message: %s '%s' QoS=%s properties=%s. Broadcasted to %d ws clients",
            topic,
            payload.decode(),
            qos,
            properties,
            num_clients_send_to,
        )
        return num_clients_send_to

    app.include_router(mqtt_router)

    return app


application = create_app()
