import os
import ssl
import uuid
import asyncio
import traceback
from ssl import SSLContext
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional, Type, Union
from fastapi import FastAPI
from gmqtt import Message
from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311,MQTTv50
from .config import MQTTConfig
try:
    from uvicorn.config import logger
    log_info = logger
except:
    import logging
    log_info = logging.getLogger()

class FastMQTT:
    '''
        FastMQTT client object to establish connection parameters before connect and manipulate MQTT service.

        The class object holds session information necesseary to connect MQTT broker.
        ```
        param :: config : MQTTConfig config class
        type  :: config: MQTTConfig
        ```
        ```
        param :: client_id : client_id  "should be unique identfiyer for connection to MQTT broker"
        type  :: client_id: Any
        ```
        ```
        param :: clean_session :    "The clean session flag tells the broker whether the client wants to establish \
                                    a persistent session or not. In a persistent session clean_session = False, the broker stores all subscriptions for the client and \
                                    all missed messages for the client that subscribed with a Quality of Service (QoS) level 1 or 2. \
                                    If the session is not persistent (clean_session = True),the broker does not store anything for the client and \
                                    purges all information from any previous persistent session.The client_id that the client provides when it establishes connection to the broker identifies the session."
        type  :: clean_session: bool
        ```
        ```
        param :: optimistic_acknowledgement :  #TODO more info needed
        type  :: optimistic_acknowledgement: bool
        ```
    '''
    def __init__(
        self,
        config: MQTTConfig,
        *,
        client_id:  Optional[str] = None,
        clean_session: bool = True,
        optimistic_acknowledgement: bool = True,
        **kwargs: Any
    ) -> None:
        if not client_id: client_id = uuid.uuid4().hex

        self.client: MQTTClient = MQTTClient(client_id,**kwargs)
        self.config: Dict[Any,Any] = config

        self.client._clean_session = clean_session
        self.client._username: Optional[str] = config.username or None
        self.client._password: Optional[str] = config.password or None
        self.client._host: str =  config.host
        self.client._port: int =  config.port
        self.client._keepalive: int = config.keepalive
        self.client._ssl: Union[bool,SSLContext]  =  config.ssl
        self.client.optimistic_acknowledgement: bool = optimistic_acknowledgement
        self.client._connect_properties: Any = kwargs
        self.client.on_message: Callable = self.__on_message
        self.client.on_connect: Callable = self.__on_connect
        self.user_message_handler = None
        self.user_connect_handler = None
        self.handlers = dict()

        log_info = logger

        if self.config.will_message_topic and self.config.will_message_payload and self.config.will_delay_interval:
            self.client._will_message = Message(
                self.config.will_message_topic,
                self.config.will_message_payload,
                self.config.will_delay_interval)
            log_info.debug(f"topic -> {self.config.will_message_topic} \n payload -> {self.config.will_message_payload} \n will_delay_interval -> {self.config.will_delay_interval}")
            log_info.debug("WILL MESSAGE INITIALIZED")

    @staticmethod
    def match(topic, template):
        '''
            publish method

            param :: topic : topic name
            type  :: topic:  str

            param :: template : template topic name that contains wildcards
            type  :: template:  str
        '''
        topic = topic.split("/")
        template = template.split("/")

        if len(topic) < len(template):
            return False

        topic_idx = 0
        for template_idx, part in enumerate(template):
            if part == "#":
                return True
            elif part == "+" or part == topic[topic_idx]:
                topic_idx += 1
                continue
            elif not part == topic[topic_idx]:
                return False

        if topic_idx == len(topic):
            return True
        return False

    async def connection(self) -> None:

        if self.client._username:
            self.client.set_auth_credentials(self.client._username, self.client._password)
            log_info.debug("user is authenticated")

        await self.__set_connetion_config()

        version = self.config.version or MQTTv50
        log_info.warning(f"Used broker version is {version}")

        await self.client.connect(self.client._host,self.client._port,self.client._ssl,self.client._keepalive,version)
        log_info.debug("connected to broker..")

    async def __set_connetion_config(self) -> None:
        '''
            By default, connected MQTT client will always try to reconnect in case of lost connections.
            Number of reconnect attempts is unlimited. If you want to change this behaviour ass reconnect_retries and reconnect_delay with its values.
            For more info: # https://github.com/wialon/gmqtt#reconnects
        '''

        if self.config.reconnect_retries:
            self.client.set_config(reconnect_retries=self.config.reconnect_retries)

        if self.config.reconnect_delay:
            self.client.set_config(reconnect_delay=self.config.reconnect_delay)

    def __on_connect(self, client, flags, rc, properties) -> None:
        '''
            Generic on connect handler, it would call user handler if defined, and will perform subscription for given topics. It cannot be done
            earlier, since subscription relies on connection
        '''
        if self.user_connect_handler:
            self.user_connect_handler(client, flags, rc, properties)

        for topic in self.handlers.keys():
            log_info.debug(f"Subscribing for {topic}")
            self.client.subscribe(topic)

    async def __on_message(self, client, topic, payload, qos, properties):
        '''
            Generic on message handler, it will call user handler if defined, and will invoke per topic handlers that is subscribed for
        '''
        gather = []
        if self.user_message_handler:
            log_info.debug(f"Calling user_message_handler")
            gather.append(self.user_message_handler(client, topic, payload, qos, properties))

        for topic_template in self.handlers.keys():
            if self.match(topic, topic_template):
                log_info.debug(f"Calling specific handler for topic {topic}")
                for handler in self.handlers[topic_template]:
                    gather.append(handler(client, topic, payload, qos, properties))

        return await asyncio.gather(*gather)

    def subscribe(self, *topics):
        '''
            Decorator method used to subscribe for specific topics
        '''

        def subscribe_handler(handler: Callable) -> Callable:
            log_info.debug(f"Subscribe for a topics: {topics}")
            for topic in topics:
                if topic not in self.handlers.keys():
                    self.handlers[topic] = []

                # TODO: Consider changing to weak_ref
                self.handlers[topic].append(handler)
            return handler

        return subscribe_handler

    def on_message(self) -> Callable[..., Any]:
        '''
            Decarator method used to subscirbe messages from all topics.
        '''

        def message_handler(handler: Callable) -> Callable:
            log_info.debug("on_message handler accepted")
            self.user_message_handler = handler
            return handler
        return message_handler


    def publish(self, message_or_topic: str, payload: Any = None, qos: int = 0, retain: bool = False, **kwargs):
        '''
            publish method

            param :: message_or_topic : topic name
            type  :: message_or_topic:  str

            param :: payload : message payload
            type  :: payload: Any

            param :: qos : Quality of Assuarance
            type  :: qos:

            param :: retain :
            type  :: retain:
        '''

        return self.client.publish(message_or_topic, payload=payload, qos=qos, retain=retain, **kwargs)

    def unsubscribe(self, topic: str, **kwargs):

        '''
            unsubscribe method

            param :: topic : topic name
            type  :: str:
        '''

        func = partial(self.client.unsubscribe, topic, **kwargs)
        log_info.debug("unsubscribe")
        if topic in self.handlers.keys():
            del self.handlers[topic]

        return self.client.unsubscribe( topic, **kwargs)

    def on_connect(self) -> Callable[..., Any]:
        '''
        Decarator method used to handle connection to MQTT.
        '''
        def connect_handler(handler: Callable) -> Callable:
            log_info.debug("handler accepted")
            self.user_connect_handler = handler

            return handler
        return connect_handler


    def on_subscribe(self) -> Callable[..., Any]:
        '''
        Decarator method used to obtain subscibred topics and properties.
        '''

        def subscribe_handler(handler: Callable):
            log_info.debug("on_subscribe handler accepted")
            self.client.on_subscribe = handler
            return handler
        return subscribe_handler


    def on_disconnect(self) -> Callable[..., Any]:
        '''
        Decarator method used wrap disconnet callback.
        '''

        def disconnect_handler(handler: Callable) -> Callable:
            log_info.debug("on_disconnect handler accepted")
            self.client.on_disconnect = handler
            return handler
        return disconnect_handler


    def init_app(self, app: FastAPI) -> None:
        @app.on_event("startup")
        async def startup():
            await self.connection()
          
        
        @app.on_event("shutdown")   
        async def shutdown():
            await self.client.disconnect()



