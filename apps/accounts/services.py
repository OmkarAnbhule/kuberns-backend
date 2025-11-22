"""
GitHub OAuth authentication service
"""

import httpx
import secrets
from typing import Dict, Optional, Tuple
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import sync_to_async

User = get_user_model()


class GitHubOAuthService:
    """Service for handling GitHub OAuth authentication"""

    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_REFRESH_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"

    def __init__(self):
        self.client_id = getattr(settings, "GITHUB_CLIENT_ID", None)
        self.client_secret = getattr(settings, "GITHUB_CLIENT_SECRET", None)
        self.redirect_uri = getattr(
            settings,
            "GITHUB_REDIRECT_URI",
            "http://localhost:8000/api/accounts/auth/github/callback",
        )

    def get_auth_url(self) -> Dict[str, str]:
        """
        Generate GitHub OAuth authorization URL

        Returns:
            Dict with auth_url and state
        """
        if not self.client_id:
            raise ValueError("GITHUB_CLIENT_ID not configured")

        state = secrets.token_urlsafe(32)
        # Store state in cache for 10 minutes
        cache.set(f"github_oauth_state_{state}", True, 600)

        # Request additional scopes for repo and org access
        scopes = "read:user,repo,user:email,read:org"
        
        auth_url = (
            f"{self.GITHUB_AUTH_URL}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes}"
            f"&state={state}"
        )

        return {"auth_url": auth_url, "state": state}

    async def exchange_code_for_token(
        self, code: str, state: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from GitHub
            state: State parameter for CSRF protection

        Returns:
            Dict with token data or None if failed
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("GitHub OAuth credentials not configured")

        # Verify state parameter
        if state:
            cached_state = await sync_to_async(cache.get)(f"github_oauth_state_{state}")
            if not cached_state:
                raise ValueError("Invalid or expired state parameter")
            await sync_to_async(cache.delete)(f"github_oauth_state_{state}")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        headers = {"Accept": "application/json", "User-Agent": "Kuberns-App"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GITHUB_TOKEN_URL, data=data, headers=headers
                )
                response.raise_for_status()

                token_data = response.json()
                return token_data

        except httpx.RequestError as e:
            print(f"GitHub token exchange failed: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh GitHub access token using refresh token

        Args:
            refresh_token: GitHub refresh token

        Returns:
            Dict with new token data or None if failed
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("GitHub OAuth credentials not configured")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        headers = {"Accept": "application/json", "User-Agent": "Kuberns-App"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GITHUB_REFRESH_URL, data=data, headers=headers
                )
                response.raise_for_status()

                token_data = response.json()
                return token_data

        except httpx.RequestError as e:
            print(f"GitHub token refresh failed: {e}")
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from GitHub API

        Args:
            access_token: GitHub access token

        Returns:
            User info dict or None if failed
        """
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
            "User-Agent": "Kuberns-App",
        }

        try:
            async with httpx.AsyncClient() as client:
                # Get user info
                user_response = await client.get(self.GITHUB_USER_URL, headers=headers)
                user_response.raise_for_status()
                user_data = user_response.json()
                print(user_data)

                # Get user emails
                emails_response = await client.get(
                    f"{self.GITHUB_USER_URL}/emails", headers=headers
                )
                print("403 body:", emails_response.text)
                print("Response headers:", dict(emails_response.headers))
                emails_response.raise_for_status()
                emails_data = emails_response.json()

                # Find primary email
                primary_email = None
                for email in emails_data:
                    if email.get("primary", False):
                        primary_email = email.get("email")
                        break

                return {
                    "id": str(user_data.get("id")),
                    "username": user_data.get("login"),
                    "email": primary_email or user_data.get("email"),
                    "name": user_data.get("name"),
                    "avatar_url": user_data.get("avatar_url"),
                }

        except httpx.RequestError as e:
            print(f"GitHub user info request failed: {e}")
            return None

    async def store_user_tokens(
        self, user: User, token_data: Dict
    ) -> None:
        """
        Store GitHub OAuth tokens in user model

        Args:
            user: User instance
            token_data: Token data from GitHub OAuth
        """
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data.get("expires_in", 28800)  # Default 8 hours
        scope = token_data.get("scope", "")
        
        user.github_access_token = access_token
        user.github_refresh_token = refresh_token
        user.github_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        user.github_token_scope = scope
        
        await sync_to_async(user.save)(
            update_fields=[
                "github_access_token",
                "github_refresh_token", 
                "github_token_expires_at",
                "github_token_scope"
            ]
        )
    
    async def ensure_valid_token(self, user: User) -> Optional[str]:
        """
        Ensure user has a valid GitHub access token, refresh if needed

        Args:
            user: User instance

        Returns:
            Valid access token or None if refresh failed
        """
        # Check if token is still valid
        if user.has_github_access():
            return user.github_access_token
        
        # Try to refresh token
        if not user.github_refresh_token:
            return None
        
        token_data = await self.refresh_access_token(user.github_refresh_token)
        if not token_data:
            return None
        
        # Store new tokens
        await self.store_user_tokens(user, token_data)
        
        return token_data.get("access_token")

    async def create_or_update_user(
        self, github_user_info: Dict, token_data: Optional[Dict] = None
    ) -> User:
        """
        Create or update user based on GitHub info

        Args:
            github_user_info: User info from GitHub API

        Returns:
            User instance
        """
        github_id = github_user_info["id"]
        github_username = github_user_info["username"]
        email = github_user_info["email"]
        name = github_user_info.get("name", "")
        avatar_url = github_user_info.get("avatar_url", "")

        # Try to find existing user by GitHub ID
        try:
            user = await sync_to_async(User.objects.get)(github_id=github_id)
            # Update existing user
            user.github_username = github_username
            user.github_avatar_url = avatar_url
            if email and not user.email:
                user.email = email
            if name and not user.display_name:
                user.display_name = name
            await sync_to_async(user.save)()
            
            # Store tokens if provided
            if token_data:
                await self.store_user_tokens(user, token_data)
            
            return user

        except User.DoesNotExist:
            # Try to find by email
            if email:
                try:
                    user = await sync_to_async(User.objects.get)(email=email)
                    # Link GitHub account to existing user
                    user.github_id = github_id
                    user.github_username = github_username
                    user.github_avatar_url = avatar_url
                    if name and not user.display_name:
                        user.display_name = name
                    await sync_to_async(user.save)()
                    
                    # Store tokens if provided
                    if token_data:
                        await self.store_user_tokens(user, token_data)
                    
                    return user
                except User.DoesNotExist:
                    pass

            # Create new user
            username = github_username
            # Ensure username is unique
            counter = 1
            while await sync_to_async(User.objects.filter(username=username).exists)():
                username = f"{github_username}_{counter}"
                counter += 1

            user = await sync_to_async(User.objects.create_user)(
                username=username,
                email=email or "",
                display_name=name or github_username,
                github_id=github_id,
                github_username=github_username,
                github_avatar_url=avatar_url,
            )
            
            # Store tokens if provided
            if token_data:
                await self.store_user_tokens(user, token_data)
            
            return user
