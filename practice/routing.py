from django.urls import path
from .consumers import PodTerminalConsumer

websocket_urlpatterns = [
    path("ws/practice/<int:course_id>/", PodTerminalConsumer.as_asgi()),
]
