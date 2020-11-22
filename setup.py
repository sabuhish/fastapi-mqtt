import setuptools
import fastapi_mqtt

with open("README.md", "r") as fh:
    long_description = fh.read()


CLASSIFIERS=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
]

 

setuptools.setup(
    name="fastapi-mqtt",
    version=fastapi_mqtt.__version__,
    author=fastapi_mqtt.__author__,
    author_email=fastapi_mqtt.__email__,
    description="fastapi-mqtt is extension for MQTT protocol",
    keywords='fastapi-mqtt, fastapimqtt', 
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/sabuhish/fastapi-mqtt",
    install_requires=["gmqtt>=0.6.8","uvicorn>=0.12.2", 'pydantic>=1.7.2',"fastapi>=0.61.2"],
    platforms=['any'],
    packages=setuptools.find_packages(),
    download_url="https://github.com/sabuhish/fastapi-mqtt",
    classifiers=CLASSIFIERS,
    python_requires='>=3.6',
    project_urls={  
        'Bug Reports': 'https://github.com/sabuhish/fastapi-mqtt/issues',
        'Say Thanks!': 'https://github.com/sabuhish/fastapi-mqtt/graphs/contributors',
        'Source': 'https://github.com/sabuhish/fastapi-mqtt',
    },
)
