from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        max_length=254,
        unique=True
    )
    username = models.CharField(
        max_length=150,
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
    )
    last_name = models.CharField(
        max_length=150,
    )
    is_subscribed = models.BooleanField(
        default=False,
    )

    @property
    def is_admin(self):
        return self.is_staff

    def __str__(self):
        return self.username
