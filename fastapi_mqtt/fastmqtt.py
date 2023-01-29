import asyncio
import uuid
from functools import partial
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI
from gmqtt import Client as MQTTClient
from gmqtt import Message
from gmqtt.mqtt.constants import MQTTv50

from .config import MQTTConfig
from .handlers import MQTTHandlers

try:
    from uvicorn.config import logger

    log_info = logger
except ImportError:
    import logging

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
    """

    def __init__(
        self,
        config: MQTTConfig,
        *,
        client_id: Optional[str] = None,
        clean_session: bool = True,
        optimistic_acknowledgement: bool = True,
        **kwargs: Any,
    ):
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
        self.handlers: Dict[str, Any] = dict()
        self.mqtt_handlers = MQTTHandlers(self.client, self.handlers)
        log_info = logger

        if (
            self.config.will_message_topic
            and self.config.will_message_payload
            and self.config.will_delay_interval
        ):
            self.client._will_message = Message(
                self.config.will_message_topic,
                self.config.will_message_payload,
                self.config.will_delay_interval,
            )
            log_info.debug(
                f'topic -> {self.config.will_message_topic} \n payload -> {self.config.will_message_payload} \n will_delay_interval -> {self.config.will_delay_interval}'  # noqa E501
            )
            log_info.debug('WILL MESSAGE INITIALIZED')

    @staticmethod
    def match(topic, template):
        """
        Defined match topics

        topic: topic name
        template: template topic name that contains wildcards
        """
        topic = topic.split('/')
        template = template.split('/')

        topic_idx = 0
        for part in template:
            if part == '#':
                return True
            elif part in ['+', topic[topic_idx]]:
                topic_idx += 1
            else:
                return False

        if topic_idx == len(topic):
            return True
        return False

    async def connection(self) -> None:

        if self.client._username:
            self.client.set_auth_credentials(self.client._username, self.client._password)
            log_info.debug('user is authenticated')

        await self.__set_connetion_config()

        version = self.config.version or MQTTv50
        log_info.warning(f'Used broker version is {version}')

        await self.client.connect(
            self.client._host,
            self.client._port,
            self.client._ssl,
            self.client._keepalive,
            version,
        )
        log_info.debug('connected to broker..')

    async def __set_connetion_config(self) -> None:
        """
        The connected MQTT clients will always try to reconnect in case of lost connections.
        The number of reconnect attempts is unlimited.
        For changing this behavior, set reconnect_retries and reconnect_delay with its values.
        For more info: https://github.com/wialon/gmqtt#reconnects
        """
        if self.config.reconnect_retries:
            self.client.set_config(reconnect_retries=self.config.reconnect_retries)

        if self.config.reconnect_delay:
            self.client.set_config(reconnect_delay=self.config.reconnect_delay)

    def __on_connect(self, client, flags, rc, properties) -> None:
        """
        Generic on connecting handler, it would call user handler if defined.
        Will perform subscription for given topics.
        It cannot be done earlier, since subscription relies on connection.
        """
        if self.mqtt_handlers.get_user_connect_handler:
            self.mqtt_handlers.get_user_connect_handler(client, flags, rc, properties)

        for topic in self.handlers.keys():
            log_info.debug(f'Subscribing for {topic}')
            self.client.subscribe(topic)

    async def __on_message(self, client, topic, payload, qos, properties):
        """
        Generic on message handler, it will call user handler if defined.
        This will invoke per topic handlers that are subscribed for
        """
        gather = []
        if self.mqtt_handlers.get_user_message_handler:
            log_info.debug('Calling user_message_handler')
            gather.append(
                self.mqtt_handlers.get_user_message_handler(client, topic, payload, qos, properties)
            )

        for topic_template in self.handlers.keys():
            if self.match(topic, topic_template):
                log_info.debug(f'Calling specific handler for topic {topic}')
                for handler in self.handlers[topic_template]:
                    gather.append(handler(client, topic, payload, qos, properties))

        return await asyncio.gather(*gather)

    def publish(
        self,
        message_or_topic: str,
        payload: Any = None,
        qos: int = 0,
        retain: bool = False,
        **kwargs,
    ):
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
        partial(self.client.unsubscribe, topic, **kwargs)
        log_info.debug('unsubscribe')
        if topic in self.handlers.keys():
            del self.handlers[topic]

        return self.client.unsubscribe(topic, **kwargs)

    def init_app(self, app: FastAPI) -> None:
        @app.on_event('startup')
        async def startup():
            await self.connection()

        @app.on_event('shutdown')
        async def shutdown():
            await self.client.disconnect()

    def subscribe(self, *topics) -> Callable[..., Any]:
        """
        Decorator method used to subscribe for specific topics.
        """

        def subscribe_handler(handler: Callable) -> Callable:
            log_info.debug(f'Subscribe for a topics: {topics}')
            for topic in topics:
                if topic not in self.handlers.keys():
                    self.handlers[topic] = []
                # TODO: Consider changing to weak_ref
                self.handlers[topic].append(handler)
            return handler

        return subscribe_handler

    def on_connect(self) -> Callable[..., Any]:
        """
        Decorator method used to handle the connection to MQTT.
        """

        def connect_handler(handler: Callable) -> Callable:
            log_info.debug('handler accepted')
            return self.mqtt_handlers.on_connect(handler)

        return connect_handler

    def on_message(self) -> Callable[..., Any]:
        """
        The decorator method is used to subscribe to messages from all topics.
        """

        def message_handler(handler: Callable) -> Callable:
            log_info.debug('on_message handler accepted')
            return self.mqtt_handlers.on_message(handler)

        return message_handler

    def on_disconnect(self) -> Callable[..., Any]:
        """
        The Decorator method used wrap disconnect callback.
        """

        def disconnect_handler(handler: Callable) -> Callable:
            log_info.debug('on_disconnect handler accepted')
            return self.mqtt_handlers.on_disconnect(handler)

        return disconnect_handler

    def on_subscribe(self) -> Callable[..., Any]:
        """
        Decorator method is used to obtain subscribed topics and properties.
        """

        def subscribe_handler(handler: Callable):
            log_info.debug('on_subscribe handler accepted')
            return self.mqtt_handlers.on_subscribe(handler)

        return subscribe_handler
