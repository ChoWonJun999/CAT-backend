from django.db import models
from django.conf import settings


class Profile(models.Model):
    """
        
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=50, null=True)
    access_key = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)

    class Meta:
        db_table = "profile"
        