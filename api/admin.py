from django.contrib import admin
from django.conf import settings
from .models import *

# admin.site.register(settings.AUTH_USER_MODEL)
admin.site.register(Profile)
admin.site.register(Order)