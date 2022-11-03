# external
import pytest


@pytest.fixture(autouse=True)
def _media_root(settings, tmpdir_factory) -> None:
    """Forces django to save media files into temp folder."""
    settings.MEDIA_ROOT = tmpdir_factory.mktemp('media', numbered=True)


@pytest.fixture(autouse=True)
def _password_hashers(settings) -> None:
    """Forces django to use fast password hashers for tests."""
    settings.PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]


@pytest.fixture(autouse=True)
def _auth_backends(settings) -> None:
    """Deactivates security backend from Axes app."""
    settings.AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)


@pytest.fixture(autouse=True)
def _debug(settings) -> None:
    """Sets proper DEBUG and TEMPLATE debug mode for coverage."""
    settings.DEBUG = False
    for template in settings.TEMPLATES:
        template['OPTIONS']['debug'] = True


@pytest.fixture()
def main_heading() -> str:
    """An example fixture containing some html fragment."""
    return '<h1>wemake-django-template</h1>'
