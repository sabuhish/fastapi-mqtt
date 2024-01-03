import logging
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

import pytest
import pytest_asyncio
from async_asgi_testclient import TestClient
from fastapi import FastAPI
from gmqtt import Client as MQTTClient

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

# Run MQTT broker in background for tests with:
# `docker run -d -p 9001:9001 -p 1883:1883 eclipse-mosquitto:1.6.15`
# set `TEST_BROKER_HOST=localhost` to use against a local broker
TEST_BROKER_HOST = os.getenv("TEST_BROKER_HOST", default="test.mosquitto.org")
TEST_BROKER_USER = "testuser" if TEST_BROKER_HOST != "test.mosquitto.org" else None
TEST_BROKER_PWD = "secret" if TEST_BROKER_HOST != "test.mosquitto.org" else None


@pytest.fixture
def test_app():  # noqa: C901
    """Fixture with example fastAPI app for tests."""
    mqtt_config = MQTTConfig(
        host=TEST_BROKER_HOST,
        will_message_topic="/WILL",
        will_message_payload="MQTT Connection is dead!",
        will_delay_interval=2,
        username=TEST_BROKER_USER,
        password=TEST_BROKER_PWD,
    )
    fast_mqtt = FastMQTT(config=mqtt_config)
    received_msgs = defaultdict(int)
    processed_msgs = defaultdict(int)

    @asynccontextmanager
    async def _lifespan(_application: FastAPI):
        await fast_mqtt.mqtt_startup()
        logging.info("connection done, starting fastapi app now")
        yield
        await fast_mqtt.mqtt_shutdown()

    app = FastAPI(lifespan=_lifespan)

    @fast_mqtt.on_connect()
    def _connect(client: MQTTClient, flags: int, rc: int, properties: Any):
        client.subscribe("fastapi-mqtt")  # subscribing mqtt topic
        logging.info("Connected: %s %s %s %s", client, flags, rc, properties)

    @fast_mqtt.subscribe("$share/test/mqtt/+/temperature", "mqtt/+/humidity")
    async def _decorated_subscription(
        client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
    ):
        """Subscription handler for temperature and humidity topics."""
        processed_msgs[topic] += 1
        logging.info(
            "temperature/humidity: %s %s %s %s",
            topic,
            payload.decode(),
            qos,
            properties,
        )
        return 0

    @fast_mqtt.subscribe("mqtt/+/humidity", qos=2)
    async def _second_subscription(
        client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
    ):
        """
        Second subscription handler for humidity topic.

        Both handlers should be called when receiving mqtt/+/humidity messages.
        """
        processed_msgs[topic] += 1
        logging.info(
            "humidity: %s %s %s %s",
            topic,
            payload.decode(),
            qos,
            properties,
        )
        return 0

    @fast_mqtt.on_message()
    async def _process_message(
        client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
    ):
        """Universal handler for all messages received."""
        received_msgs[topic] += 1
        logging.info(
            "Received message: %s %s %s %s",
            topic,
            payload.decode(),
            qos,
            properties,
        )
        return 0

    @fast_mqtt.on_disconnect()
    def _disconnect(client: MQTTClient, packet, exc=None):
        logging.info("Disconnected")

    @fast_mqtt.on_subscribe()
    def _subscribe(client: MQTTClient, mid: int, qos: int, properties: Any):
        logging.info("subscribed %s %s %s %s", client, mid, qos, properties)

    @app.get("/test-status")
    async def _get_status():
        return {
            "received_msgs": received_msgs,
            "processed_msgs": processed_msgs,
            "num_subscriptions": len(fast_mqtt.subscriptions),
        }

    @app.post("/test-publish")
    async def _pub_msg():
        fast_mqtt.publish("fastapi-mqtt", "Hello from Fastapi")
        fast_mqtt.publish("mqtt/test/temperature", "27ºC")
        fast_mqtt.publish("mqtt/test/humidity", "0%")
        return {"result": True, "message": "Published"}

    @app.post("/test-unsubscribe")
    async def _unsub():
        fast_mqtt.unsubscribe("fastapi-mqtt")
        fast_mqtt.unsubscribe("$share/test/mqtt/+/temperature")
        return {"result": True, "message": "Unsubscribed"}

    @app.post("/test-reset")
    async def _reset_msgs():
        fast_mqtt.publish("fastapi-mqtt")
        fast_mqtt.publish("mqtt/test/humidity")
        fast_mqtt.publish("mqtt/test/temperature")
        return {"result": True, "message": "Cleaned"}

    return app


@pytest_asyncio.fixture
async def app_client(test_app):
    """FastApi TestClient with example app."""
    async with TestClient(test_app) as tc:
        yield tc
