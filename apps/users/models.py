# external
from django.contrib.auth.models import AbstractUser

# project
from apps.core.models import BaseModel


class User(BaseModel, AbstractUser):
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']
