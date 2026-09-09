from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from drf_spectacular.views import SpectacularSwaggerView

from gateway.openapi import get_openapi_schema


def openapi_schema(request):
    return JsonResponse(get_openapi_schema())


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/schema",
        openapi_schema,
        name="schema",
    ),

    path(
        "api/docs",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),

    path(
        "api/",
        include("gateway.urls"),
    ),
]