from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
import httpx

from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings



ROUTES = {
    "auth": settings.USER_SERVICE_URL,
    "profile": settings.USER_SERVICE_URL,
    "movies": settings.MOVIE_SERVICE_URL,
    "watchlist": settings.MOVIE_SERVICE_URL,
    "watched": settings.MOVIE_SERVICE_URL,
    "sessions": settings.SESSION_SERVICE_URL,
    "recommendations": settings.CHAT_SERVICE_URL,
}

PROTECTED_ROUTES = {
    "profile",
    "movies",
    "watchlist",
    "watched",
    "sessions",
    "recommendations",
}



@method_decorator(csrf_exempt, name="dispatch")
class ProxyView(View):

    async def dispatch(self, request, path=""):
        service = path.split("/")[0]

        user_id = None

        if service in PROTECTED_ROUTES:
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return HttpResponse(
                    '''{
                        "error": "Authorization header is required",
                        "message": "Please provide a valid Bearer token."
                    }''',
                    status=401,
                    content_type="application/json",
                )

            try:
                token_type, raw_token = auth_header.split(" ", 1)

                if token_type.lower() != "bearer":
                    return HttpResponse(
                        '''{
                            "error": "Invalid authorization header",
                            "message": "Please provide a valid header"
                        }''',
                        status=403
                    )

                token = AccessToken(raw_token)

                user_id = token.get("user_id")

            except (ValueError, TokenError, KeyError):
                return HttpResponse(
                    '''{
                        "error": "Invalid or expired token", 
                        "message": "Please provide a valid access token"
                    }''',
                    status=403
                )

        service_url = ROUTES.get(service)

        if not service_url:
            return HttpResponse(
                "Route not found",
                status=404
            )

        target_path = path

        target_url = f"{service_url}/api/{target_path}"

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {
                "host",
                "content-length",
                "x-user-id",
            }
        }

        if user_id is not None:
            headers["X-User-ID"] = str(user_id)

        timeout = httpx.Timeout(30.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=request.body,
                headers=headers,
                params=request.GET,
            )

        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers.get(
                "Content-Type",
                "application/json",
            ),
        )