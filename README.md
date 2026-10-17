# fastapi-mqtt

MQTT is a lightweight publish/subscribe messaging protocol designed for M2M (machine to machine) telemetry in low bandwidth environments.
Fastapi-mqtt is the client for working with MQTT.

For more information about MQTT, please refer to here: [MQTT](https://sabuhish.github.io/fastapi-mqtt/mqtt/)

Fastapi-mqtt wraps around the [gmqtt](https://github.com/wialon/gmqtt) module, a Python async MQTT client.
The module supports the MQTT version 5.0 protocol.

[![MIT licensed](https://img.shields.io/github/license/sabuhish/fastapi-mqtt)](https://github.com/sabuhish/fastapi-mqtt/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt)
[![GitHub forks](https://img.shields.io/github/forks/sabuhish/fastapi-mqtt.svg)](https://github.com/sabuhish/fastapi-mqtt/forks)
[![GitHub issues](https://img.shields.io/github/issues-raw/sabuhish/fastapi-mqtt)](https://github.com/sabuhish/fastapi-mqtt/issues)

---

## **Documentation**: [FastApi-MQTT](https://sabuhish.github.io/fastapi-mqtt/)

The key features are:

- Subscribe to topics with decorated handlers, publish to topics
- Pydantic models for message payloads, to receive and publish typed messages
- MQTT 5.0, with callbacks for connection events
- MQTT settings with a `pydantic` class, authentication to the broker with credentials

### 🔨 Installation

Requires Python 3.12 or newer.

```sh
pip install fastapi-mqtt
```

Next: [Getting Started](https://sabuhish.github.io/fastapi-mqtt/getting-started/),
[Configuration](https://sabuhish.github.io/fastapi-mqtt/configuration/),
[Pydantic Models](https://sabuhish.github.io/fastapi-mqtt/models/),
[Advanced](https://sabuhish.github.io/fastapi-mqtt/advanced/).

# Contributing

Feel free to open issues and send pull requests.

Thanks To [Contributors](https://github.com/sabuhish/fastapi-mqtt/graphs/contributors).
Contributions of any kind are welcome!

Before you start please read [CONTRIBUTING](https://github.com/sabuhish/fastapi-mqtt/blob/master/CONTRIBUTING.md),
which also explains how to run the tests and the examples.
