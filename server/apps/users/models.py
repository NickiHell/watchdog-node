from django.contrib.auth.models import AbstractUser

from server.apps.core.models import BaseModel


class User(AbstractUser, BaseModel):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
