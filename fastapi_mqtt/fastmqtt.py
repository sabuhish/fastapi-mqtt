
from gmqtt import Client as MQTTClient
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, Union
from pydantic import  BaseSettings
import ssl
from ssl import SSLContext
from gmqtt.mqtt.constants import MQTTv311,MQTTv50
import uuid



class MQQTConfig(BaseSettings):
    
    '''
    MQQTConfig is main the configuration to be passsed client object.

    host : To connect MQQT broker, defaults to localhost
    port : To connect MQQT broker, defaults to 1883

    ssl : if given and not false, a SSL/TLS transport is created (by default a plain TCP transport is created)
        If ssl is a ssl.SSLContext object, this context is used to create the transport; if ssl is True, a default context returned from ssl.create_default_context() is used.

    keepalive : Maximum period in seconds between communications with the broker. 
        If no other messages are being exchanged, this controls the rate at which
        the client will send ping messages to the broker the keepalive timeout value for the client. Defaults to 60 seconds.

    username : username for authentication, defaults to None
    password : password for authentication, defaults to None

    version : MQTT broker version to use, defaults to  MQTTv50. 
        According to gmqtt.Client if your broker does not support 5.0 protocol version and responds with proper CONNACK reason code, client will downgrade to 3.1 and reconnect automatically.

    reconnect_retries && reconnect_delay : By default, connected MQTT client will always try to reconnect in case of lost 
        connections. Number of reconnect attempts is unlimited. 
        If you want to change this behaviour pass reconnect_retries and reconnect_delay with its values. 
        For more info: # https://github.com/wialon/gmqtt#reconnects
   
    '''
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

        param :: optimistic_acknowledgement : 
        type  :: optimistic_acknowledgement: bool
       
        param :: will_message : this message will be published by broker after client disconnects 
           
        type  :: will_message: str
        '''

        if not client_id: client_id = uuid.uuid4().hex

        self.client: MQTTClient = MQTTClient(client_id)
        self.config: Dict[Any,Any] = config

        self.client._clean_session: bool = True
        self.client._username: Optional[str] = config.get("username") if  config.get("username") else None
        self.client._password: Optional[str] = config.get("password") if  config.get("password") else None
        self.client._host: str =  config.get("localhost")
        self.client._port: int =  config.get("port")
        self.client._keepalive: int = config.get("keepalive")
        
        self.client._ssl: Union[bool,SSLContext]  =  config.get("ssl")

        self.client.optimistic_acknowledgement: bool = optimistic_acknowledgement
        self.client._connect_properties: Any = kwargs

        self.client._will_message: str = will_message


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
