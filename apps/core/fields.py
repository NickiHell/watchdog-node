# external
from django.db import models


class CreatedField(models.DateTimeField):
    """Created datetime field."""

    def __init__(self, **kwargs):
        kwargs['auto_now_add'] = True
        kwargs['editable'] = False
        super().__init__(**kwargs)


class ModifiedField(models.DateTimeField):
    """Modified datetime field."""

    def __init__(self, **kwargs):
        kwargs['auto_now'] = True
        kwargs['editable'] = False
        super().__init__(**kwargs)
