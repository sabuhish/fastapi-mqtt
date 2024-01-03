import asyncio
import logging
import uuid
from itertools import zip_longest
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import FastAPI
from gmqtt import Client as MQTTClient
from gmqtt import Message, Subscription
from gmqtt.mqtt.constants import MQTTv50

from .config import MQTTConfig
from .handlers import MQTTHandlers

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

    optimistic_acknowledgement:  #TODO more info needed

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
        **kwargs: Any,
    ) -> None:
        if not client_id:
            client_id = uuid.uuid4().hex

        self.client: MQTTClient = MQTTClient(client_id, **kwargs)
        self.config: MQTTConfig = config

        self.client._clean_session = clean_session
        self.client._username = config.username
        self.client._password = config.password
        self.client._host = config.host
        self.client._port = config.port
        self.client._keepalive = config.keepalive
        self.client._ssl = config.ssl
        self.client.optimistic_acknowledgement = optimistic_acknowledgement
        self.client._connect_properties = kwargs
        self.client.on_message = self.__on_message
        self.client.on_connect = self.__on_connect
        self.subscriptions: Dict[str, Tuple[Subscription, List[Callable]]] = {}
        self._logger = mqtt_logger or log_info
        self.mqtt_handlers = MQTTHandlers(self.client, self._logger)

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
                "WILL MESSAGE INITIALIZED: "
                "topic -> %s\n payload -> %s\n will_delay_interval -> %s",
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
        """
        if self.mqtt_handlers.user_connect_handler is not None:
            self.mqtt_handlers.user_connect_handler(client, flags, rc, properties)

        for topic in self.subscriptions:
            self._logger.debug("Subscribing for %s", topic)
            self.client.subscribe(self.subscriptions[topic][0])

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
        **kwargs,
    ) -> None:
        """
        Defined to publish payload MQTT server

        message_or_topic: topic name

        payload: message payload

        qos: Quality of Assurance

        retain:
        """
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

    async def mqtt_shutdown(self) -> None:
        """Final disconnection for MQTT client, for lifespan shutdown."""
        await self.client.disconnect()

    def init_app(self, app: FastAPI) -> None:  # pragma: no cover
        """Add startup and shutdown event handlers for app without lifespan."""

        @app.on_event("startup")
        async def startup() -> None:
            await self.mqtt_startup()

        @app.on_event("shutdown")
        async def shutdown() -> None:
            await self.mqtt_shutdown()

    def subscribe(
        self,
        *topics,
        qos: int = 0,
        no_local: bool = False,
        retain_as_published: bool = False,
        retain_handling_options: int = 0,
        subscription_identifier: Any = None,
    ) -> Callable[..., Any]:
        """
        Decorator method used to subscribe for specific topics.
        """

        def subscribe_handler(handler: Callable) -> Callable:
            self._logger.debug("Subscribe for topics: %s", topics)
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
                    self.subscriptions[topic] = (subscription, [handler])
                else:
                    # Use the most restrictive field of the same subscription
                    old_subscription = self.subscriptions[topic][0]
                    new_subscription = Subscription(
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
                    self.subscriptions[topic] = (
                        new_subscription,
                        self.subscriptions[topic][1],
                    )
                    self.subscriptions[topic][1].append(handler)
            return handler

        return subscribe_handler

    def on_connect(self) -> Callable[..., Any]:
        """
        Decorator method used to handle the connection to MQTT.
        """

        def connect_handler(handler: Callable) -> Callable:
            self._logger.debug("handler accepted")
            return self.mqtt_handlers.on_connect(handler)

        return connect_handler

    def on_message(self) -> Callable[..., Any]:
        """
        The decorator method is used to subscribe to messages from all topics.
        """

        def message_handler(handler: Callable) -> Callable:
            self._logger.debug("on_message handler accepted")
            return self.mqtt_handlers.on_message(handler)

        return message_handler

    def on_disconnect(self) -> Callable[..., Any]:
        """
        The Decorator method used wrap disconnect callback.
        """

        def disconnect_handler(handler: Callable) -> Callable:
            self._logger.debug("on_disconnect handler accepted")
            return self.mqtt_handlers.on_disconnect(handler)

        return disconnect_handler

    def on_subscribe(self) -> Callable[..., Any]:
        """
        Decorator method is used to obtain subscribed topics and properties.
        """

        def subscribe_handler(handler: Callable):
            self._logger.debug("on_subscribe handler accepted")
            return self.mqtt_handlers.on_subscribe(handler)

        return subscribe_handler
