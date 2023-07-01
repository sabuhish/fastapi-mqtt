import logging
import os
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from async_asgi_testclient import TestClient
from fastapi import FastAPI

from fastapi_mqtt.config import MQTTConfig
from fastapi_mqtt.fastmqtt import FastMQTT

# Run MQTT broker in background for tests with:
# `docker run -d --name mosquitto -p 9001:9001 -p 1883:1883 eclipse-mosquitto:1.6.15`
# set `TEST_BROKER_HOST=localhost` to use against a local broker
TEST_BROKER_HOST = os.getenv('TEST_BROKER_HOST', default='test.mosquitto.org')
TEST_BROKER_USER = 'testuser' if TEST_BROKER_HOST != 'test.mosquitto.org' else None
TEST_BROKER_PWD = 'secret' if TEST_BROKER_HOST != 'test.mosquitto.org' else None


@pytest.fixture
def test_app():
    """Fixture with example fastAPI app for tests."""
    mqtt_config = MQTTConfig(
        host=TEST_BROKER_HOST,
        will_message_topic='/WILL',
        will_message_payload='MQTT Connection is dead!',
        will_delay_interval=2,
        username=TEST_BROKER_USER,
        password=TEST_BROKER_PWD,
    )
    fast_mqtt = FastMQTT(config=mqtt_config)

    @asynccontextmanager
    async def _lifespan(application: FastAPI):
        await fast_mqtt.connection()
        logging.info('connection done, starting fastapi app now')
        yield
        await fast_mqtt.client.disconnect()

    app = FastAPI(lifespan=_lifespan)

    @fast_mqtt.on_connect()
    def _connect(client, flags, rc, properties):
        fast_mqtt.client.subscribe('mqtt')  # subscribing mqtt topic
        logging.info('Connected: %s %s %s %s', client, flags, rc, properties)

    @fast_mqtt.subscribe('mqtt/+/temperature', 'mqtt/+/humidity')
    async def _decorated_subscription(client, topic, payload, qos, properties):
        logging.info('temperature/humidity: %s %s %s %s', topic, payload.decode(), qos, properties)
        return 0

    @fast_mqtt.on_message()
    async def _process_message(client, topic, payload, qos, properties):
        logging.info('Received message: %s %s %s %s', topic, payload.decode(), qos, properties)
        return 0

    @fast_mqtt.on_disconnect()
    def _disconnect(client, packet, exc=None):
        logging.info('Disconnected')

    @fast_mqtt.on_subscribe()
    def _subscribe(client, mid, qos, properties):
        logging.info('subscribed %s %s %s %s', client, mid, qos, properties)

    @app.post('/test-publish')
    async def _pub_msg():
        fast_mqtt.publish('mqtt', 'Hello from Fastapi')
        fast_mqtt.publish('mqtt/test/humidity', '0%')
        return {'result': True, 'message': 'Published'}

    @app.post('/test-unsubscribe')
    async def _unsub():
        fast_mqtt.unsubscribe('mqtt')
        fast_mqtt.unsubscribe('mqtt/+/temperature')
        return {'result': True, 'message': 'Unsubscribed'}

    @app.post('/test-reset')
    async def _reset_msgs():
        fast_mqtt.publish('mqtt')
        fast_mqtt.publish('mqtt/test/humidity')
        return {'result': True, 'message': 'Cleaned'}

    return app


@pytest_asyncio.fixture
async def client(test_app):
    """FastApi TestClient with example app."""
    async with TestClient(test_app) as tc:
        yield tc
