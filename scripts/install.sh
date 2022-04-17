#!/bin/bash

# Installing dependencies for fastapi-mqtt, thanks for contirbuting if you have any issues feel free to open.
# Issue URL https://github.com/sabuhish/fastapi-mqtt/issues

set -e

CURRENT_DIRECTORY=$(pwd)

CURRENT_USER=$(whoami)
VERSION="1.0.0"

README_URL="https://github.com/sabuhish/fastapi-mqtt"

echo -e "Staring to create environment and installing dependencies for fastapi-mqtt"

function install(){

    sudo -u $CURRENT_USER bash << EOF 
        echo -e "\ncreating virtualenv ..."
       
        cd .. 
        python3 -m venv .venv
        source .venv/bin/activate
        
        pip install --upgrade pip

        echo "installing dependencies"

        pip install "fastapi>=0.61.2" 'uvicorn>=0.12.2' 'gmqtt>=0.6.8'  "pydantic>=1.7.2" 
         
        DIRECTORY=$(pwd)

        touch $DIRECTORY/app.py    

echo "
from fastapi_mqtt.fastmqtt import FastMQTT
from fastapi import FastAPI
from fastapi_mqtt.config import MQTTConfig

mqtt_config = MQTTConfig()

fast_mqtt = FastMQTT(config=mqtt_config)

app = FastAPI()

@app.on_event('startup')
async def startapp():
    await fast_mqtt.connection()

@app.on_event('shutdown')
async def shutdown():
    await fast_mqtt.client.disconnect()

@fast_mqtt.on_connect()
def connect(client, flags, rc, properties):
    fast_mqtt.client.subscribe('/mqtt') #subscribing mqtt topic 
    print('Connected:', client, flags, rc, properties)

@fast_mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print('Received message:',topic, payload.decode(), qos, properties)
    return 0

@fast_mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print('Disconnected')

@fast_mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print('subscribed', client, mid, qos, properties)

@app.get('/')
async def func():
    fast_mqtt.publish('/mqtt', 'Hello from Fastapi') #publishing mqtt topic 

    return {'result': True,'message':'Published' }" >> app.py
        
        echo ""
        echo -e "fastapi-mqtt: $VERSION"
      
        echo -e "\nYou are ready to work on it, do the last things:"
        echo -e "source .venv/bin/activate"
        echo -e "cat app.py"
      

        echo -e "\nPlease see the README file for more information:"
        echo ""
        echo -e "$README_URL\n\n"
        echo -e "You can also run with uvicorn:"
        echo ""
        echo -e "uvicorn app:app --port 8000 --reload" 
        cd $CURRENT_DIRECTORY
        exit 0

EOF
}

install

