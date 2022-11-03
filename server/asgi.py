# built-in
import os

# external
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = get_asgi_application()
