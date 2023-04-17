from typing import Any, Callable, Optional

from gmqtt import Client as MQTTClient

try:
    from uvicorn.config import logger

    log_info = logger
except ImportError:
    import logging

    log_info = logging.getLogger()


class MQTTHandlers:
    def __init__(self, client: MQTTClient, handlers: dict):
        self.client = client
        self.handlers = handlers
        self.user_message_handler: Optional[Callable[..., Any]] = None
        self.user_connect_handler: Optional[Callable[..., Any]] = None

    def on_message(self, handler: Callable) -> Callable[..., Any]:
        log_info.info('on_message handler accepted')
        self.user_message_handler = handler
        return handler

    def on_subscribe(self, handler: Callable) -> Callable[..., Any]:
        """
        Decorator method is used to obtain subscribed topics and properties.
        """
        log_info.info('on_subscribe handler accepted')
        self.client.on_subscribe = handler
        return handler

    def on_disconnect(self, handler: Callable) -> Callable[..., Any]:
        self.client.on_disconnect = handler
        return handler

    def on_connect(self, handler: Callable) -> Callable[..., Any]:
        log_info.info('on_connect handler accepted')
        self.user_connect_handler = handler
        return handler

    @property
    def get_user_message_handler(self) -> Optional[Callable[..., Any]]:
        return self.user_message_handler

    @property
    def get_user_connect_handler(self) -> Optional[Callable[..., Any]]:
        return self.user_connect_handler
