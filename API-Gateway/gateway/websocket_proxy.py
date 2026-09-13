import asyncio
import websockets
import json
from urllib.parse import parse_qs

from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


async def websocket_proxy(scope, receive, send):

    # Browsers cannot set custom headers (like Authorization) on native
    # WebSocket connections, so the client sends the token as a query
    # param instead (e.g. ?token=...). Read it from there.
    query_params = parse_qs(scope.get("query_string", b"").decode())
    raw_token = (query_params.get("token") or [None])[0]

    if not raw_token:
        await send({
            "type": "websocket.close",
            "code": 4001,
        })
        return

    try:
        token = AccessToken(raw_token)

        user_id = token["user_id"]

    except (ValueError, TokenError, KeyError):

        await send({
            "type": "websocket.accept",
        })

        await send({
            "type": "websocket.send",
            "text": json.dumps({
                "type": "error",
                "error": "Invalid or expired token",
                "message": "Please provide a valid access token."
            })
        })

        await send({
            "type": "websocket.close",
            "code": 4001,
        })

        return

    session_service_url = (
        f"{settings.SESSION_SERVICE_URL.replace('http', 'ws')}"
        f"{scope['path']}"
    )

    # Keep query string if there is one
    if scope.get("query_string"):
        session_service_url += f"?{scope['query_string'].decode()}"

    async with websockets.connect(
        session_service_url,
        additional_headers={
            "X-User-ID": str(user_id),
        },
    ) as backend_ws:

        async def client_to_backend():
            while True:
                message = await receive()

                if message["type"] == "websocket.disconnect":
                    await backend_ws.close()
                    break

                if message["type"] == "websocket.receive":

                    if "text" in message:
                        await backend_ws.send(message["text"])

                    elif "bytes" in message:
                        await backend_ws.send(message["bytes"])

        async def backend_to_client():
            try:
                while True:
                    message = await backend_ws.recv()

                    if isinstance(message, str):
                        await send({
                            "type": "websocket.send",
                            "text": message,
                        })
                    else:
                        await send({
                            "type": "websocket.send",
                            "bytes": message,
                        })

            except websockets.exceptions.ConnectionClosed:
                pass

        # Send trusted user ID to Session Service
        # Session Service does NOT trust the client for this ID.
        await send({
            "type": "websocket.accept",
        })

        await asyncio.gather(
            client_to_backend(),
            backend_to_client(),
        )