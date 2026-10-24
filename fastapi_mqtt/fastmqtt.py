import asyncio
import inspect
import logging
import uuid
from itertools import zip_longest
from typing import Any, Callable, Dict, List, Optional, Tuple

from gmqtt import Client as MQTTClient
from gmqtt import Message, Subscription
from gmqtt.mqtt.constants import MQTTv50
from pydantic import BaseModel, ValidationError

from .codecs import Codec, JSONCodec
from .config import MQTTConfig
from .handlers import (
    MQTTConnectionHandler,
    MQTTDisconnectHandler,
    MQTTHandlers,
    MQTTMessageHandler,
    MQTTPayloadErrorHandler,
    MQTTSubscriptionHandler,
)
from .payloads import describe_errors, handler_name, model_spec

try:
    from uvicorn.config import logger as log_info
except ImportError:
    log_info = logging.getLogger()


class FastMQTT:
    """
    FastMQTT client sets connection parameters before connecting and manipulating the MQTT service.
    The object holds session information necessary to connect the MQTT broker.

    config: MQTTConfig config object

    client_id: Should be a unique identifier for connection to the MQTT broker.

    clean_session: Enables broker to establish a persistent session.
                            In a persistent session clean_session = False.
                            The broker stores all subscriptions for the client.
                            If the session is not persistent (clean_session = True).
                            The broker does not store anything for the client and \
                            purges all information from any previous persistent session.
                            The client_id  identifies the session.

    optimistic_acknowledgement: If True (default), QoS 1/2 messages are acknowledged
                            before the message handlers run. If False, they are acknowledged
                            after the handlers finish. Only applies to MQTT 5.0.

    mqtt_logger: Optional logging.Logger to use.
    """

    def __init__(
        self,
        config: MQTTConfig,
        *,
        client_id: Optional[str] = None,
        clean_session: bool = True,
        optimistic_acknowledgement: bool = True,
        mqtt_logger: Optional[logging.Logger] = None,
        codec: Optional[Codec] = None,
        **kwargs: Any,
    ) -> None:
        if not client_id:
            client_id = uuid.uuid4().hex

        self.client: MQTTClient = MQTTClient(
            client_id,
            clean_session=clean_session,
            optimistic_acknowledgement=optimistic_acknowledgement,
            **kwargs,
        )
        self.config: MQTTConfig = config

        self.client._username = config.username
        self.client._password = config.password
        self.client._host = config.host
        self.client._port = config.port
        self.client._keepalive = config.keepalive
        self.client._ssl = config.ssl
        self.client._connect_properties = kwargs
        self.client.on_message = self.__on_message
        self.client.on_connect = self.__on_connect
        self.subscriptions: Dict[str, Tuple[Subscription, List[MQTTMessageHandler]]] = {}
        self._logger = mqtt_logger or log_info
        self.mqtt_handlers = MQTTHandlers(self.client, self._logger)
        # CONNACK args of the last successful connection, to call late `on_connect` handlers
        self._connack: Optional[Tuple[int, int, Any]] = None
        self.codec: Codec = codec or JSONCodec()

        if (
            self.config.will_message_topic
            and self.config.will_message_payload
            and self.config.will_delay_interval
        ):
            self.client._will_message = Message(
                self.config.will_message_topic,
                self.config.will_message_payload,
                will_delay_interval=self.config.will_delay_interval,
            )
            self._logger.debug(
                "WILL MESSAGE INITIALIZED: topic -> %s\n payload -> %s\n will_delay_interval -> %s",
                self.config.will_message_topic,
                self.config.will_message_payload,
                self.config.will_delay_interval,
            )

    @staticmethod
    def match(topic: str, template: str) -> bool:
        """
        Defined match topics

        topic: topic name
        template: template topic name that contains wildcards
        """
        if str(template).startswith("$share/"):
            template = template.split("/", 2)[2]

        topic_parts = topic.split("/")
        template_parts = template.split("/")

        for topic_part, part in zip_longest(topic_parts, template_parts):
            if part == "#" and not str(topic_part).startswith("$"):
                return True
            elif (topic_part is None or part not in {"+", topic_part}) or (
                part == "+" and topic_part.startswith("$")
            ):
                return False
            continue

        return len(template_parts) == len(topic_parts)

    async def connection(self) -> None:
        if self.client._username:
            self.client.set_auth_credentials(self.client._username, self.client._password)
            self._logger.debug("user is authenticated")

        await self.__set_connetion_config()

        version = self.config.version or MQTTv50
        self._logger.info("Used broker version is %s", version)

        await self.client.connect(
            self.client._host,
            self.client._port,
            self.client._ssl,
            self.client._keepalive,
            version,
        )
        self._logger.debug("Connected to broker")

    async def __set_connetion_config(self) -> None:
        """
        The connected MQTT clients will always try to reconnect in case of lost connections.
        The number of reconnect attempts is unlimited.
        For changing this behavior, set reconnect_retries and reconnect_delay with its values.
        For more info: https://github.com/wialon/gmqtt#reconnects
        """
        self.client.set_config(
            {
                "reconnect_retries": self.config.reconnect_retries,
                "reconnect_delay": self.config.reconnect_delay,
            }
        )

    def __on_connect(self, client: MQTTClient, flags: int, rc: int, properties: Any) -> None:
        """
        Generic on connecting handler, it would call user handler if defined.
        Will perform subscription for given topics.
        It cannot be done earlier, since subscription relies on connection.
        Registered topics are subscribed before calling the user handler, so topics
        registered from inside it are subscribed once, by the `subscribe` decorator.
        """
        self._connack = (flags, rc, properties)
        for topic in list(self.subscriptions):
            self._logger.debug("Subscribing for %s", topic)
            self.client.subscribe(self.subscriptions[topic][0])

        if self.mqtt_handlers.user_connect_handler is not None:
            self.mqtt_handlers.user_connect_handler(client, flags, rc, properties)

    async def __on_message(
        self, client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
    ) -> Any:
        """
        Generic on message handler, it will call user handler if defined.
        This will invoke per topic handlers that are subscribed for
        """
        gather = []
        if self.mqtt_handlers.user_message_handler is not None:
            self._logger.debug("Calling user_message_handler")
            gather.append(
                self.mqtt_handlers.user_message_handler(client, topic, payload, qos, properties)
            )

        for topic_template in self.subscriptions:
            if self.match(topic, topic_template):
                self._logger.debug("Calling specific handler for topic %s", topic)
                for handler in self.subscriptions[topic_template][1]:
                    gather.append(handler(client, topic, payload, qos, properties))

        return await asyncio.gather(*gather)

    def publish(
        self,
        message_or_topic: str,
        payload: Any = None,
        qos: int = 0,
        retain: bool = False,
        codec: Optional[Codec] = None,
        **kwargs,
    ) -> None:
        """
        Defined to publish payload MQTT server

        message_or_topic: topic name

        payload: message payload. A pydantic model is sent as JSON.

        qos: Quality of Assurance

        retain:
        """
        if isinstance(payload, BaseModel):
            payload = (codec or self.codec).encode(payload)
        return self.client.publish(
            message_or_topic, payload=payload, qos=qos, retain=retain, **kwargs
        )

    def unsubscribe(self, topic: str, **kwargs):
        """
        Defined to unsubscribe topic

        topic: topic name
        """
        self._logger.debug("unsubscribe")
        if topic in self.subscriptions:
            del self.subscriptions[topic]

        return self.client.unsubscribe(topic, **kwargs)

    async def mqtt_startup(self) -> None:
        """Initial connection for MQTT client, for lifespan startup."""
        await self.connection()

    async def mqtt_shutdown(self, reason_code: int = 0, **properties: Any) -> None:
        """
        Final disconnection for MQTT client, for lifespan shutdown.

        reason_code: MQTT 5.0 DISCONNECT reason code, defaults to 0 (normal disconnection).
            For example, 4 (disconnect with will message) asks the broker to publish
            the will message. Ignored with MQTT 3.1.1.
        properties: MQTT 5.0 DISCONNECT properties, like `reason_string`.
        """
        await self.client.disconnect(reason_code, **properties)

    def init_app(self, fastapi_app) -> None:  # pragma: no cover
        """Add startup and shutdown event handlers for app without lifespan."""

        @fastapi_app.on_event("startup")
        async def startup() -> None:
            await self.mqtt_startup()

        @fastapi_app.on_event("shutdown")
        async def shutdown() -> None:
            await self.mqtt_shutdown()

    def _message_handler(self, handler: Callable[..., Any], codec: Codec) -> MQTTMessageHandler:
        """
        Adapt a subscription handler to the generic message handler call.

        Handlers without a parameter typed as a pydantic model are called as usual,
        with (client, topic, payload, qos, properties). For a handler with one,
        the payload is parsed into that model, and the other parameters are passed
        by name, from client, topic, payload, qos and properties.
        Messages with an invalid payload go to the `on_payload_error` handler,
        or are logged and skipped.
        """
        spec = model_spec(handler)
        if spec is None:
            return handler
        model_param, model, args = spec

        async def model_handler(
            client: MQTTClient, topic: str, payload: bytes, qos: int, properties: Any
        ) -> Any:
            try:
                item = codec.decode(model=model, payload=payload)
            except ValidationError as error:
                await self._payload_error(handler, client, topic, payload, error)
                return None
            values = {
                "client": client,
                "topic": topic,
                "payload": payload,
                "qos": qos,
                "properties": properties,
            }
            return await handler(**{model_param: item}, **{param: values[param] for param in args})

        return model_handler

    async def _payload_error(
        self,
        handler: Callable[..., Any],
        client: MQTTClient,
        topic: str,
        payload: bytes,
        error: ValidationError,
    ) -> None:
        error_handler = self.mqtt_handlers.user_payload_error_handler
        if error_handler is None:
            self._logger.warning(
                "Invalid payload on topic %s for handler %s: %s",
                topic,
                handler_name(handler),
                describe_errors(error),
            )
            return
        result = error_handler(client, topic, payload, error)
        if inspect.isawaitable(result):
            await result

    def subscribe(
        self,
        *topics,
        qos: int = 0,
        no_local: bool = False,
        retain_as_published: bool = False,
        retain_handling_options: int = 0,
        subscription_identifier: Any = None,
        codec: Optional[Codec] = None,
    ) -> Callable[..., Any]:
        """
        Decorator method used to subscribe for specific topics.

        Topics are subscribed on every (re)connection. If the client is already
        connected when the decorator runs, they are also subscribed right away.

        Handlers get (client, topic, payload, qos, properties). If a handler has a
        parameter typed as a pydantic model, the payload is parsed into that model instead,
        and the other parameters are passed by name:

            @mqtt.subscribe("sensors/+/temperature")
            async def temperature(item: Temperature, topic: str): ...
        """

        def subscribe_handler(handler: MQTTMessageHandler) -> MQTTMessageHandler:
            self._logger.debug("Subscribe for topics: %s", topics)
            message_handler = self._message_handler(handler, codec or self.codec)
            for topic in topics:
                if topic not in self.subscriptions:
                    subscription = Subscription(
                        topic,
                        qos,
                        no_local,
                        retain_as_published,
                        retain_handling_options,
                        subscription_identifier,
                    )
                    self.subscriptions[topic] = (subscription, [message_handler])
                else:
                    # Use the most restrictive field of the same subscription
                    old_subscription, handlers = self.subscriptions[topic]
                    subscription = Subscription(
                        topic,
                        max(qos, old_subscription.qos),
                        no_local or old_subscription.no_local,
                        retain_as_published or old_subscription.retain_as_published,
                        max(
                            retain_handling_options,
                            old_subscription.retain_handling_options,
                        ),
                        old_subscription.subscription_identifier or subscription_identifier,
                    )
                    handlers.append(message_handler)
                    self.subscriptions[topic] = (subscription, handlers)

                if self.client.is_connected:
                    self._logger.debug("Already connected, subscribing for %s", topic)
                    self.client.subscribe(subscription)
            return handler

        return subscribe_handler

    def on_connect(self) -> Callable[..., Any]:
        """
        Decorator method used to handle the connection to MQTT.

        The handler runs on every (re)connection. If the client is already
        connected when the decorator runs, it is also called right away
        with the CONNACK args of the current connection.
        """

        def connect_handler(handler: MQTTConnectionHandler) -> MQTTConnectionHandler:
            self._logger.debug("handler accepted")
            self.mqtt_handlers.on_connect(handler)
            if self.client.is_connected and self._connack is not None:
                self._logger.debug("Already connected, calling on_connect handler")
                handler(self.client, *self._connack)
            return handler

        return connect_handler

    def on_message(self) -> Callable[..., Any]:
        """
        The decorator method is used to subscribe to messages from all topics.
        """

        def message_handler(handler: MQTTMessageHandler) -> MQTTMessageHandler:
            self._logger.debug("on_message handler accepted")
            return self.mqtt_handlers.on_message(handler)

        return message_handler

    def on_payload_error(self) -> Callable[..., Any]:
        """
        Decorator method used to handle messages with a payload that is not valid
        for the pydantic model of a subscription handler.

        The handler gets (client, topic, payload, error), with the pydantic ValidationError.
        Without it, these messages are logged as a warning and skipped.
        """

        def payload_error_handler(handler: MQTTPayloadErrorHandler) -> MQTTPayloadErrorHandler:
            self._logger.debug("on_payload_error handler accepted")
            return self.mqtt_handlers.on_payload_error(handler)

        return payload_error_handler

    def on_disconnect(self) -> Callable[..., Any]:
        """
        The Decorator method used wrap disconnect callback.
        """

        def disconnect_handler(handler: MQTTDisconnectHandler) -> MQTTDisconnectHandler:
            self._logger.debug("on_disconnect handler accepted")
            return self.mqtt_handlers.on_disconnect(handler)

        return disconnect_handler

    def on_subscribe(self) -> Callable[..., Any]:
        """
        Decorator method is used to obtain subscribed topics and properties.
        """

        def subscribe_handler(handler: MQTTSubscriptionHandler) -> MQTTSubscriptionHandler:
            self._logger.debug("on_subscribe handler accepted")
            return self.mqtt_handlers.on_subscribe(handler)

        return subscribe_handler
