from django.contrib import admin

# Register your models here.
from server.apps.users.models import User

admin.register(User)
