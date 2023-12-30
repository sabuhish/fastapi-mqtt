from typing import Annotated

from fastapi import APIRouter, Depends, Request, WebSocket

from .mqtt_ws_client import DynamicMQTTClient

mqtt_router = APIRouter()


async def _get_ws_subscribers(request: Request) -> DynamicMQTTClient:
    return request.app.state.ws_subscribers


async def _get_ws_subscribers_from_ws(websocket: WebSocket) -> DynamicMQTTClient:
    return websocket.app.state.ws_subscribers


Clients = Annotated[DynamicMQTTClient, Depends(_get_ws_subscribers)]
WSClients = Annotated[DynamicMQTTClient, Depends(_get_ws_subscribers_from_ws)]
