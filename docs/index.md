# FastApi-MQTT

## Extension

MQTT is a lightweight publish/subscribe messaging protocol designed for M2M (machine to machine) telemetry in low bandwidth environments.
Fastapi-mqtt is the client for working with MQTT.

For more information about MQTT, please refer to here: [MQTT](mqtt.md)

Fastapi-mqtt wraps around the [gmqtt](https://github.com/wialon/gmqtt) module, a Python async MQTT client.
The module supports the MQTT version 5.0 protocol.

## Badges

[![MIT licensed](https://img.shields.io/github/license/sabuhish/fastapi-mqtt)](https://github.com/sabuhish/fastapi-mqtt/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt)
[![GitHub forks](https://img.shields.io/github/forks/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt/forks)
[![GitHub issues](https://img.shields.io/github/issues-raw/sabuhish/fastapi-mqtt)](https://github.com/sabuhish/fastapi-mqtt/issues)

## Available Features

- Subscribe to topics with decorated handlers, publish to topics
- [Pydantic models](models.md) for message payloads, to receive and publish typed messages
- MQTT 5.0, with [callbacks](advanced.md#connection-callbacks) for connection events
- MQTT settings with a `pydantic` class, authentication to the broker with credentials
