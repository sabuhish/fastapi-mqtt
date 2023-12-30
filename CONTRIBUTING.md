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

```sh
git clone https://github.com/sabuhish/fastapi-mqtt.git
cd fastapi-mqtt
poetry install
# activate the poetry virtualenv
poetry shell
# to make changes and validate them
pre-commit install
pre-commit install-hooks
pre-commit run --all-files
# to run the test suite
pytest
```

Explore the fastapi app **examples** and run them with uvicorn

```sh
uvicorn examples.app:app --port 8000 --reload
```

NOTE: Be sure to merge the latest from "upstream" before making a pull request!

### Code formatting

This project uses `pre-commit` to apply multiple linters to the code changes _before_ it's commited.

You can invoke it anytime by running `pre-commit run --all-files`.

Install the hook with `pre-commit install-hooks` to trigger it when commiting changes.
