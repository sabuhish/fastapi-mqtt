import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from uvicorn.config import logger

from .dependencies import Clients, WSClients

mqtt_router = APIRouter()

_HTML_WS_MQTT_CLIENT = """<!DOCTYPE html>
<html>
    <head>
        <title>MQTT WebSocket Client</title>
    </head>
    <body>
        <h1>WebSocket Dynamic MQTT client</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="topicText" autocomplete="off"/>
            <button>Subscribe to topic</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket(`ws://localhost:8000/ws-mqtt-client`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            function sendMessage(event) {
                var input = document.getElementById("topicText");
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""


@mqtt_router.get("/home")
async def _ws_demo_page():
    """Show basic web with websocket connection to subscribe to MQTT topics."""
    return HTMLResponse(_HTML_WS_MQTT_CLIENT)


@mqtt_router.get("/ws-subscriptions")
async def _get_current_clients_subscriptions(ws_subscribers: Clients):
    """Return JSON with current state of WS clients."""
    return {
        "topic_subscriptions": list(ws_subscribers.topic_subscriptions.keys()),
        "clients_by_topic": {
            key: len(queues) for key, queues in ws_subscribers.topic_subscriptions.items()
        },
    }


@mqtt_router.websocket("/ws-mqtt-client")
async def websocket_endpoint(websocket: WebSocket, ws_subscribers: WSClients):
    await websocket.accept()
    logger.info("WS connected")

    async def _send_received_msgs(topic):
        async for msg in ws_subscribers.subscribe(topic):
            await websocket.send_text(msg)

    try:
        data_topic = await websocket.receive_text()
        logger.warning("WS MQTT subscription to '%s'", data_topic)

        await websocket.send_text(f"You subscribed to: {data_topic}")
        while True:
            # in separate task, listen to received MQTT messages
            task_push_msg = asyncio.create_task(
                _send_received_msgs(data_topic),
            )
            # while waiting for new WS socket for new MQTT subscription
            data_topic = await websocket.receive_text()
            task_push_msg.cancel()
            logger.warning("WS MQTT subscription change to '%s'", data_topic)
            await websocket.send_text(f"You subscribed to: {data_topic}")
    except WebSocketDisconnect:
        logger.info("Closed tab")
