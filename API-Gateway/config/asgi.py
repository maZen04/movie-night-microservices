import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

django_application = get_asgi_application()

from gateway.websocket_proxy import websocket_proxy


async def application(scope, receive, send):
    if scope["type"] == "websocket" and scope["path"].startswith("/ws/"):
        await websocket_proxy(scope, receive, send)
    else:
        await django_application(scope, receive, send)