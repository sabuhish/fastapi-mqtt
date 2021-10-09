__author__ = "Sabuhi Shukurov"

__email__ = 'sabuhi.shukurov@gmail.com'

credits = ["Sabuhi Shukurov","Hasan Aliyev", "Tural Muradov", "vincentto13", "Jeremy T. Hetzel"]

__version__ = "0.4.0"

from sys import modules as imported_modules
if not "setuptools" in imported_modules.keys():
    from fastapi_mqtt.fastmqtt import FastMQTT
    from fastapi_mqtt.config import  MQTTConfig, MQQTConfig

    __all__ = ["FastMQTT", "MQTTConfig", "MQQTConfig"]
