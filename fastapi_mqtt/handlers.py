import warnings
from logging import Logger
from typing import Any, Awaitable, Callable, Optional

from gmqtt import Client as MQTTClient

# client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
MQTTMessageHandler = Callable[[MQTTClient, str, bytes, int, Any], Awaitable[Any]]
# client: MQTTClient, flags: int, rc: int, properties: Any
MQTTConnectionHandler = Callable[[MQTTClient, int, int, Any], Any]
# client: MQTTClient, mid: int, qos: int, properties: Any
MQTTSubscriptionHandler = Callable[[MQTTClient, int, int, Any], Any]
# client: MQTTClient, topic: str, payload: bytes, error: pydantic.ValidationError
MQTTPayloadErrorHandler = Callable[[MQTTClient, str, bytes, Any], Any]
# client: MQTTClient, packet: bytes, exc=None
MQTTDisconnectHandler = Callable[[MQTTClient, bytes, Optional[Exception]], Any]


class MQTTHandlers:
    def __init__(self, client: MQTTClient, logger: Logger):
        self._logger = logger
        self.client = client
        self.user_message_handler: Optional[MQTTMessageHandler] = None
        self.user_connect_handler: Optional[MQTTConnectionHandler] = None
        self.user_payload_error_handler: Optional[MQTTPayloadErrorHandler] = None

    def on_message(self, handler: MQTTMessageHandler) -> MQTTMessageHandler:
        self._logger.info("on_message handler accepted")
        self.user_message_handler = handler
        return handler

    def on_subscribe(self, handler: MQTTSubscriptionHandler) -> MQTTSubscriptionHandler:
        """
        Decorator method is used to obtain subscribed topics and properties.
        """
        self._logger.info("on_subscribe handler accepted")
        self.client.on_subscribe = handler
        return handler

    def on_disconnect(self, handler: MQTTDisconnectHandler) -> MQTTDisconnectHandler:
        self.client.on_disconnect = handler
        return handler

    def on_payload_error(self, handler: MQTTPayloadErrorHandler) -> MQTTPayloadErrorHandler:
        self._logger.info("on_payload_error handler accepted")
        self.user_payload_error_handler = handler
        return handler

    def on_connect(self, handler: MQTTConnectionHandler) -> MQTTConnectionHandler:
        self._logger.info("on_connect handler accepted")
        self.user_connect_handler = handler
        return handler

    # TODO: Remove these unused properties on v3.0
    @property
    def get_user_message_handler(self) -> Optional[MQTTMessageHandler]:  # pragma: no cover
        warnings.warn(
            "Deprecated property. Access to .user_message_handler", DeprecationWarning, stacklevel=1
        )
        return self.user_message_handler

    @property
    def get_user_connect_handler(self) -> Optional[MQTTConnectionHandler]:  # pragma: no cover
        warnings.warn(
            "Deprecated property. Access to .user_connect_handler", DeprecationWarning, stacklevel=1
        )
        return self.user_connect_handler
