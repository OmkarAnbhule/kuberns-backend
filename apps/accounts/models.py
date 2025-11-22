from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.

    Note: Make sure to set AUTH_USER_MODEL = 'accounts.User' in settings.py
    """

    display_name = models.CharField(max_length=100, blank=True)
    github_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    github_username = models.CharField(max_length=100, blank=True)
    github_avatar_url = models.URLField(blank=True)

    # GitHub OAuth tokens
    github_access_token = models.TextField(
        blank=True, help_text="GitHub OAuth access token"
    )
    github_refresh_token = models.TextField(
        blank=True, help_text="GitHub OAuth refresh token"
    )
    github_token_expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Token expiration time"
    )
    github_token_scope = models.CharField(
        max_length=255, blank=True, help_text="OAuth scopes granted"
    )

    def __str__(self):
        return self.display_name or self.username

    def is_github_token_expired(self) -> bool:
        """Check if GitHub access token is expired"""
        if not self.github_token_expires_at:
            return True
        return timezone.now() >= self.github_token_expires_at

    def has_github_access(self) -> bool:
        """Check if user has valid GitHub access"""
        return bool(self.github_access_token and not self.is_github_token_expired())
