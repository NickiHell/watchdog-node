from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from health_check import urls as health_urls
from ninja import NinjaAPI


api = NinjaAPI()


@api.get('/ping')
def add(request):
    return {'result': 'pong'}


admin.autodiscover()

urlpatterns = [
    # Apps:
    path('health/', include(health_urls, namespace='health')),
    path('admin/', admin.site.urls, name='admin'),
]

if settings.DEBUG:  # pragma: no cover
    # external
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns = [
        # URLs specific only to django-debug-toolbar:
        path('__debug__/', include(debug_toolbar.urls)),
        *urlpatterns,
        # Serving media files in development only:
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]
