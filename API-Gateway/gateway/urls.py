from django.urls import path

from .views import *


urlpatterns = [
    path("<path:path>", ProxyView.as_view()),
]