from django.db import models
from django.conf import settings


class Profile(models.Model):
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=50, null=True)
    access_key = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)
    state = models.BooleanField(
        default=False
    )

    METHOD_CHOICES = [
        (0, '변동성 전략')
        , (1, '볼린저 밴드')
        , (2, '5-10')
    ]

    method = METHOD_CHOICES

    class Meta:
        db_table = "profile"

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order"