## Short Information

Short information about Message Queuing Telemetry Transport

We will cover some basics and later on will dive in advance.
This information is for beginners and for those who want to gain more knowledge.
If you don't have any knowledge of what MQTT does, go ahead you will get much more.

`MQTT` stands for Message Queuing Telemetry Transport. The protocol was invented by IBM to facilitate machine-to-machine communication. It works on the publish and subscribe model to ensure efficient communication across platforms, and also has a level system for message priority. Currently, this protocol is widely used for IoT and large-scale communication because of its small footprint and minimal bandwidth consumption.

In addition, it is designed as a lightweight messaging protocol that uses publish/subscribe operations to exchange data between clients and the server. Furthermore, its small size, low power usage, minimized data packets, and ease of implementation make the protocol ideal for the machine-to-machine or Internet of Things world.

The compact header size of MQTT and its QoS (Quality of Service) are geared toward reliable M2M communication at a fundamental level, requiring few workarounds to operate smoothly. QoS in MQTT means that each message has three levels of a check for guaranteed message delivery. The levels increase bandwidth usage as they progress, but higher QoS carries with it assurances at the highest level for critical transmissions.

So to sum up above:

- It's a lightweight protocol. So, it's easy to implement in software and fast in data transmission.
- It's based on a messaging technique.
- Minimized data packets. Hence, low network usage.
- Low power usage. As a result, it saves the connected device's battery.
- It's real-time! That is specifically what makes it perfect for IoT applications.

#### MQTT Components

- `Broker`, which is the server that handles the data transmission between the clients.
- A ` topic`, is the place a device wants to put or retrieve a message to/from.
- The message (` payload`), is the data that a device receives when subscribing to a topic or sends when publishing to a topic.
- `Publish`, is the process a device does to send its message to the broker.
- ` Subscribe`, where a device does to retrieve a message from the broker.

In MQTT a publisher publishes messages on a topic and a subscriber must subscribe to that topic to view the message. MQTT is based on clients and a server. Likewise, the server is the guy who is responsible for handling the client's requests for receiving or sending data between each other. MQTT `server` is called a `broker` and the `clients` are simply the `connected devices`. When a `device (a client)` wants to send data to the `broker`, we call this operation a `publish`. When a device (a `client`) wants to receive data from the broker, we call this operation a `subscribe`. These clients are publishing and subscribing to topics. So, the broker here is the one that handles the publishing/subscribing actions to the target topics.

##### For instance

The device has a temperature sensor. Certainly, it wants to send his readings to the broker. On the other side, a phone/desktop application wants to receive this temperature value. Therefore, 2 things will happen:
The device defines the topic it wants to publish on, ex: 'temp', then, it publishes the message 'temperature value'. The phone/desktop application subscribes to the topic 'temp', it receives the message that the device has published, which is the temperature value. Again, the broker's role here is to take the message 'temperature value' and deliver it to the phone/desktop application.

##### Important Points to note

- Clients do not have addresses like in email systems, and messages are not sent to clients.
- Messages are published to a broker on a topic.
- The job of an MQTT broker is to filter messages based on topic and then distribute them to subscribers.
- A client can receive these messages by subscribing to that topic on the same broker.
- There is no direct connection between a publisher and a subscriber.
- All clients can publish (broadcast) and subscribe (receive).
- MQTT brokers do not normally store messages.

#### MQTT Topic

Publishers publish to a broker, and the subscribers subscribe to that same broker and they subscribe to the same topic.
They will receive all messages sent by that publisher. Publisher publishes throughout the topic and subscribers listen to the same topic to retrieve it. Topics are created dynamically when someone subscribes to a topic someone publishes a message to a topic with the retained message set to True.

##### Important Notes

- `Topic names are case sensitive.
- `Use utf8`.
- `Must consist at least one character to be valid`.
- Topics do not need to begin with a `/` and in fact, stating your topic structure with a `/` is considered bad practice.

#### Subscribing to Topics

The following are all valid topic structures for houses with sensors in several rooms. It is a design choice.

```
house/room1/senson1
house/room2/sensor1
house/room2/sensor1
house-room1-sensonr1
house-room2-sensor1
house/room1-sensor1
house/room2-sensor1
```

When subscribing to multiple topics two wildcard characters can be used. Wildcards can only be used to denote a level or multi-levels i.e: `/house/#`

```
# (hash character) - multi-level wildcard
+ (plus character) - single-level wildcard
```

##### Wildcards

The client can subscribe to an individual or multiple topics. For multiple, you can use wild characters - `#` multi-level wildcard. For single-level - `+` single-level charter. Wildcards can only be used to denote level or multi-levels: i.e: `/house/#` and it will basically subscribe you all topics under that level slash house forward

Invalid Topic Subscriptions:

```
house+ - Reason no topic level
house# - Reason no topic level
```

Using wildcards:
Subscribing to topic `house/+/main-light` which subscribes to any of these topics and this time ones below room1, room2 garage covered by `+` single. You will notice they all end with main-light.

##### Example

```
house/room1/main-light
house/room2/main-light
house/garage/main-light
```

But it does not cover:

```
house/room1/side-light
house/room2/side-light
```

Because it has a side-light, it is not main-light.

#### Publishing to Topics

A client can only publish an individual topic. That is, using wildcards when publishing is not allowed. To publish a message on two topics you need to publish the message twice.

#### MQTT Protocol

In comparison to HTTP, MQTT Protocol ensures high delivery guarantees. According to measurements in 3G networks, the throughout of MQTT is 93 times faster than HTTP.

There are 3 levels of Quality of Services:

- At most once: guarantees a best-effort delivery.
- At least once: guaranteed that a message will be delivered at least once. But the message can also be delivered more than once.
- Exactly once: guarantees that each message is received only once by the counterpart

HTTP is a request-response protocol for client-server computing and is not always optimized for mobile devices. The main solid benefits of MQTT in these terms are light weightiness (MQTT transfers data as a byte array) and publish/subscribe model, which makes it perfect for resource-constrained devices and helps to save battery. MQTT is a binary-based protocol where the control elements are binary bytes and not text strings. MQTT has a very short message header and the smallest packet message size of 2 bytes.

#### MQTT specification

- CONNECT
- PUBLISH
- SUBSCRIBE
- UNSUBSCRIBE
- DISCONNECT

Whereas HTTP specifications are much longer.HTTP is worthy and extendable. But MQTT is more suitable when it is referred to as IoT development.

MQTT uses a command and command acknowledgment format. That means each command has an associated acknowledgment. Topic names, Client ID, username, and passwords are encoded as UTF-8 strings. The Payload excluding MQTT protocol information like Client ID etc. is binary data and the content and format are application-specific. The fixed header field consists of the control field and the variable-length packet length field.

The MQTT packet or message format consists of a 2-byte fixed header (always present) + Variable-header (not always present)+ payload (not always present).
It is interesting that the client ID field is sent as the first part of the payload, and not as part of the header. MQTT uses TCP/IP to connect to the broker. TCP is a connection-orientated protocol with error correction and guarantees that packets are received in order.

#### References

`https://github.com/mqtt/mqtt.github.io/wikis`

`https://blogs.windows.com/buildingapps/2016/03/14/when-to-use-a-http-call-instead-of-a-websocket-or-http-2-0/#ojUEP8d4hQBbeDVO.97`

`http://www.steves-internet-guide.com/mqtt/`
