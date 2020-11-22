### 🕹 Guide

After installing the module you setup your `FastApi` app:

Main classes are ```FastMQTT``` and ```MQQTConfig```



```python
from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQQTConfig

app = FastAPI()

mqtt_config = MQQTConfig()

mqtt = FastMQTT(
    config=mqtt_config
)

```

### ```MQQTConfig``` class
class has following attributes

-  host  : To connect MQQT broker, defaults to localhost
-  port : To connect MQQT broker, defaults to 1883
-  ssl  : if given and not false, a SSL/TLS transport is created (by default a plain TCP transport is created)
        If ssl is a ssl.SSLContext object, this context is used to create the transport; if ssl is True, a default context returned from ssl.create_default_context() is used.
- keepalive : Maximum period in seconds between communications with the broker. 
        If no other messages are being exchanged, this controls the rate at which
        the client will send ping messages to the broker the keepalive timeout value for the client. Defaults to 60 seconds.
- username : username for authentication, defaults to None 
- password : password for authentication, defaults to None
- version : MQTT broker version to use, defaults to  MQTTv50. 
        According to gmqtt.Client if your broker does not support 5.0 protocol version and responds with proper CONNACK reason code, client will downgrade to 3.1 and reconnect automatically.
- reconnect_retries
- reconnect_delay

reconnect_retries && reconnect_delay : By default, connected MQTT client will always try to reconnect in case of lost 
        connections. Number of reconnect attempts is unlimited. 
        If you want to change this behaviour pass reconnect_retries and reconnect_delay with its values. 
        For more info: # https://github.com/wialon/gmqtt#reconnects

Last three parameters is used after client disconnects abnormally 
    param :: will_message_topic : Topic of the payload
    param :: will_message_payload : The payload
    param :: will_delay_interval : Delay interval

- will_message_topic
- will_message_payload
- will_delay_interval

### ```FastMQTT``` client 

client object to establish connection parametrs beforeconnect and manipulate MQTT service. 
###  ```FastMQTT``` params
client has following parametrs. The class object holds session information necesseary to connect MQTT broker.
<!-- 


""

param :: optimistic_acknowledgement :  #TODO more info needed
type  :: optimistic_acknowledgement: bool -->

- config : MQQTConfig config class  
- client_id :  unique identfiyer for connection to MQQT broker
- clean_session : The clean session flag tells the broker whether the client wants to establish \
        a persistent session or not. In a persistent session clean_session = False, the broker stores all subscriptions for the client and \
        all missed messages for the client that subscribed with a Quality of Service (QoS) level 1 or 2. \
        If the session is not persistent (clean_session = True),the broker does not store anything for the client and \
            purges all information from any previous persistent session.The client_id that the client provides when it establishes connection to the broker identifies the session., 
- optimistic_acknowledgement



