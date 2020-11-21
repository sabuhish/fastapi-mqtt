
from gmqtt import Client as MQTTClient
from gmqtt import Message
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union
import ssl
from ssl import SSLContext
from gmqtt.mqtt.constants import MQTTv311,MQTTv50
from .config import MQQTConfig
import uuid
from functools import partial
import asyncio
from concurrent.futures import ThreadPoolExecutor


class FastMQTT:
    def __init__(
        self,
        config: MQQTConfig,  
        *, 
        client_id:  Optional[Type[str]] = None,
        clean_session: bool = True, 
        optimistic_acknowledgement: bool = True,
        **kwargs: Any
    ) -> None:

        '''
        FastMQTT client object to establish connection parametrs beforeconnect and manipulate MQTT service.
        
        The class object holds session information necesseary to connect MQTT broker.
       
        param :: config : Config parameters for gmqtt.Client
        type  :: config: MQQTConfig

        param :: client_id : client_id  should be unique identfiyer for connection to MQQT broker
        type  :: client_id: Any

        param :: clean_session : The clean session flag tells the broker whether the client wants to establish
            a persistent session or not. In a persistent session clean_session = False, the broker stores all subscriptions for the client and all missed messages for the client that subscribed with a Quality of Service (QoS) level 1 or 2. If the session is not persistent (clean_session = True), the broker does not store anything for the client and purges all information from any previous persistent session. The client_id that the client provides when it establishes connection to the broker identifies the session.
        type  :: clean_session: bool

        param :: optimistic_acknowledgement :  #TODO more info needed
        type  :: optimistic_acknowledgement: bool
        '''

        if not client_id: client_id = uuid.uuid4().hex

        self.client: MQTTClient = MQTTClient(client_id)
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
        self.executor = ThreadPoolExecutor()
        self.loop = asyncio.get_event_loop()

        if self.config.will_message_topic and self.config.will_message_payload and self.config.will_delay_interval:
            self.client._will_message = Message(
                self.config.will_message_topic, 
                self.config.will_message_payload,
                self.config.will_delay_interval
            )

    async def connection(self) -> None:
        
        if self.client._username:
         
            self.client.set_auth_credentials(self.client._username, self.client._password)

        await self.__set_connetion_config()

        version = self.config.version or MQTTv50

        await self.client.connect(self.client._host,self.client._port,self.client._ssl,self.client._keepalive,version)


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

    def on_message(self):
        """
        Decarator method used to subscirbe messages from all topics.
        """
        
        def message_handler(handler: Callable) -> Callable:
            self.client.on_message = handler
            
            return handler

        return message_handler


    async def publish(self, message_or_topic, payload=None, qos=0, retain=False, **kwargs):
        '''
            publish method
        
            param :: message_or_topic : 
            type  :: message_or_topic: 
        
            param :: payload : 
            type  :: payload: 

            param :: qos : 
            type  :: qos:  
            
            param :: retain : 
            type  :: retain:  
        '''

        loop = asyncio.get_event_loop()
        func = partial(self.client.publish, message_or_topic, payload=payload, qos=qos, retain=retain, **kwargs)
        return await loop.run_in_executor(self.executor, func)

    async def unsubscribe(self, topic: str, **kwargs):

        '''
            unsubscribe method

    def unsubscribe(self, topic: str, **kwargs):
       return self.client._connection.unsubscribe(topic, **kwargs)
            param :: retain : 
            type  :: retain:  
        '''

        func = partial(self.client.unsubscribe, topic, **kwargs)
        return await self.loop.run_in_executor(self.executor, func)
    
    def on_connect(self):
        """
        Decarator method used to handle connection to MQTT.
        """
        def connect_handler(handler: Callable) -> Callable:
            self.client.on_connect = handler
                
            return handler

        return connect_handler
    
    
    def on_subscribe(self):
        """
        Decarator method used to obtain subscibred topics and properties.
        """

        def subscribe_handler(handler: Callable):
            self.client.on_subscribe = handler
            return handler

        return subscribe_handler

     
    def on_disconnect(self):
        """
        Decarator method used wrap disconnet callback.

        """
        
        def disconnect_handler(handler: Callable) -> Callable:
            self.client.on_disconnect = handler

            return handler

        return disconnect_handler