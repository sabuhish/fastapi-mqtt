
from gmqtt import Client as MQTTClient
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union
from pydantic import  BaseSettings
import ssl
from ssl import SSLContext
from gmqtt.mqtt.constants import MQTTv311,MQTTv50
import uuid



class MQQTConfig(BaseSettings):
    host: str = "localhost"
    port: int = 1883
    ssl:  bool = False
    keepalive:  int = 60
    username: str = None
    password: str  = None
    version: int = MQTTv50

    reconnect_retries: int  = None
    reconnect_delay: int = None



class FastMQTT:
    def __init__(
        self,
        config: MQQTConfig,  
        *, 
        client_id:  Optional[Type[Any]] = None,
        clean_session: bool = True, 
        optimistic_acknowledgement: bool = True,
        will_message: str = None, 
        **kwargs: Any
    ) -> None:

        if not client_id: client_id = uuid.uuid4().hex
        
        self.client: MQTTClient = MQTTClient(client_id)



    def on_message(self):

        """
        Decarator method used to subscirbe messages from all topics.
        """
        
        def message_handler(handler: Callable) -> Callable:
            self.client.on_message = handler
            
            return handler

        return message_handler

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
