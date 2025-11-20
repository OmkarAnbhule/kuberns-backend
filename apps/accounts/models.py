from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    
    Note: Make sure to set AUTH_USER_MODEL = 'accounts.User' in settings.py
    """
    display_name = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.display_name or self.username