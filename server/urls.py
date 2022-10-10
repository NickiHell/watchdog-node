from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularSwaggerView
from health_check import urls as health_urls

admin.autodiscover()

urlpatterns = [
    # Apps:
    # Health checks:
    path('health/', include(health_urls)),  # noqa: DJ05
    # django-admin:
    path('admin/', admin.site.urls),
    path(
        'api/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]

if settings.DEBUG:  # pragma: no cover
    import debug_toolbar  # noqa: WPS433
    from django.conf.urls.static import static  # noqa: WPS433

    urlpatterns = (
        [
            # URLs specific only to django-debug-toolbar:
            path('__debug__/', include(debug_toolbar.urls)),  # noqa: DJ05
        ]
        + urlpatterns
        + static(
        # Serving media files in development only:
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
        + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # type: ignore
    )
