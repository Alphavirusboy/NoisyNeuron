"""
ASGI config for noisyneuron project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'noisyneuron.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

from audio_processor.consumers import AudioProcessingConsumer, MusicTheoryConsumer

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/audio-processing/", AudioProcessingConsumer.as_asgi()),
            path("ws/music-theory/", MusicTheoryConsumer.as_asgi()),
            # Legacy route for backward compatibility
            path("ws/processing/", AudioProcessingConsumer.as_asgi()),
        ])
    ),
})
