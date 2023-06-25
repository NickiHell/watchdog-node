"""
This is a django-split-settings core file.

For more information read this:
https://github.com/sobolevn/django-split-settings
https://sobolevn.me/2017/04/managing-djangos-settings

To change settings file:
`DJANGO_ENV=production python manage.py runserver`
"""

# built-in
from os import environ

# external
import django_stubs_ext
from split_settings.tools import include, optional


# Monkeypatching Django, so stubs will work for all generics,
# see: https://github.com/typeddjango/django-stubs
django_stubs_ext.monkeypatch()

# Managing environment via `DJANGO_ENV` variable:
environ.setdefault('DJANGO_ENV', 'dev')
_ENV = environ['DJANGO_ENV']

_base_settings = (
    'components/common.py',
    'components/logging.py',
    'components/csp.py',
    'components/caches.py',
    # Select the right env:
    f'environments/{_ENV}.py',
    # Optionally override some settings:
    optional('environments/test.py'),
)

# Include settings:
include(*_base_settings)
