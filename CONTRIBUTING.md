# Contributing to fastapi-mqtt

We welcome contributions to [fastapi-mqtt](https://github.com/sabuhish/fastapi-mqtt)

## Issues

Feel free to submit issues and enhancement requests.

[Fastapi-MQTT Issues](https://github.com/sabuhish/fastapi-mqtt/issues)

## Contributing

Please refer to each project's style and contribution guidelines for submitting patches and additions. In general, we follow the "fork-and-pull" Git workflow.

1.  **Fork** the repo on GitHub
2.  **Clone** the project to your own machine
3.  **Commit** changes to your own branch
4.  **Push** your work
5.  Submit a **Pull request** so that we can review your changes

## Before contributing, here is how to install

Requirements: Python 3.12+ and [Poetry](https://python-poetry.org/docs/#installation) 2.x.

```sh
git clone https://github.com/sabuhish/fastapi-mqtt.git
cd fastapi-mqtt
poetry install
# activate the poetry virtualenv
eval $(poetry env activate)
# to make changes and validate them
pre-commit install
pre-commit run --all-files
```

### Running tests

Tests need an MQTT broker. Run a local one with Docker, the same version used in CI:

```sh
docker run -d --rm --name mqtt -p 1883:1883 eclipse-mosquitto:1.6.15
pytest
docker stop mqtt
```

To run the tests against another broker, set its host in `TEST_BROKER_HOST`,
like `TEST_BROKER_HOST=test.mosquitto.org pytest` for the public test broker.

Explore the fastapi app **examples** and run them with uvicorn

```sh
uvicorn examples.app:app --port 8000 --reload
```

NOTE: Be sure to merge the latest from "upstream" before making a pull request!

### Code formatting

This project uses `pre-commit` to apply multiple linters to the code changes _before_ they're committed.

You can invoke it anytime by running `pre-commit run --all-files`.

Install the git hook with `pre-commit install` to trigger it when committing changes.
