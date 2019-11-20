import ssh.routing
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter


application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            ssh.routing.websocket_urlpatterns
        )
    ),
})
