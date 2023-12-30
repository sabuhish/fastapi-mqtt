import asyncio
from asyncio import Queue
from contextlib import contextmanager
from typing import AsyncGenerator, cast, Generator

from gmqtt import Subscription
from uvicorn.config import logger

from fastapi_mqtt.fastmqtt import FastMQTT


class DynamicMQTTClient:
    """
    Wrapper around FastMQTT manager to dynamically subscribe to MQTT topics

    Supporting multiple persistent connections (like websockets or SSE),
    so the MQTT client is subscribed to a certain topic only when at least
    one client is listening to MQTT messages on it.

    If multiple clients _subscribe_ to the same topic,
    the subscription is shared and all clients are notified on new messages
    that match the subscribed topic.

    Inpired by the `MultisubscriberQueue` in
    https://github.com/smithk86/asyncio-multisubscriber-queue
    """

    mqtt: FastMQTT
    topic_subscriptions: dict[str, set[Queue[str]]]
    _close_sentinel = cast(str, object())

    __slots__ = ("mqtt", "topic_subscriptions")

    def __init__(self, mqtt: FastMQTT) -> None:
        self.mqtt = mqtt
        self.topic_subscriptions = {}

    async def subscribe(
        self,
        topic: str,
        qos: int = 0,
        no_local: bool = False,
        retain_as_published: bool = False,
        retain_handling_options: int = 0,
    ) -> AsyncGenerator[str, None]:
        """Async generator to subscribe to MQTT topic and receive messages."""
        with self.queue(topic, qos, no_local, retain_as_published, retain_handling_options) as q:
            while True:
                _data: str = await q.get()
                if _data is self._close_sentinel:
                    break
                yield _data

    @contextmanager
    def queue(
        self,
        topic: str,
        qos: int,
        no_local: bool,
        retain_as_published: bool,
        retain_handling_options: int,
    ) -> Generator[Queue[str], None, None]:
        """Context helper which manages the lifecycle of the Queue."""
        _queue: Queue[str] = Queue()
        if topic in self.topic_subscriptions:
            self.topic_subscriptions[topic].add(_queue)
        else:
            self.topic_subscriptions[topic] = {_queue}
            subscription = Subscription(
                topic,
                qos,
                no_local,
                retain_as_published,
                retain_handling_options,
            )
            logger.warning("Subscribing to %s -> %s", subscription.topic, subscription)
            self.mqtt.client.subscribe(subscription)
        try:
            yield _queue
        finally:
            self.topic_subscriptions[topic].remove(_queue)
            if not self.topic_subscriptions[topic]:
                self.topic_subscriptions.pop(topic)
                logger.warning("UnSubscribing from %s", topic)
                self.mqtt.client.unsubscribe(topic)

    async def send_mqtt_msg(self, mqtt: FastMQTT, topic: str, msg_payload: str) -> int:
        """Put data on all the Queues matching the topic."""
        tasks = []
        for topic_listen, queues in self.topic_subscriptions.items():
            if mqtt.match(topic, topic_listen):
                tasks.extend(
                    [
                        _queue.put(f"Msg received in topic '{topic}':\n{msg_payload}")
                        for _queue in queues
                    ]
                )
        if tasks:
            await asyncio.gather(*tasks)
        return len(tasks)

    async def close(self) -> None:
        """Put the close sentinel on all the Queues to signal session end."""
        await asyncio.gather(
            *[
                _queue.put(self._close_sentinel)
                for queues in self.topic_subscriptions.values()
                for _queue in queues
            ]
        )
