from ninja_extra import ControllerBase, api_controller, route
from ninja_jwt.authentication import AsyncJWTAuth
from ninja_jwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseRedirect
from typing import Dict, Any, Union

from apps.core.exceptions import (
    handle_api_exception,
    BadRequestException,
    UnauthorizedException,
)
from .schemas import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema,
    LoginSchema,
    LoginResponseSchema,
    GitHubLoginSchema,
    GitHubAuthUrlSchema,
)
from .services import GitHubOAuthService

User = get_user_model()


@api_controller("/accounts", tags=["Accounts"])
class AccountsController(ControllerBase):

    @route.get("/me", response=UserSchema, auth=AsyncJWTAuth())
    @handle_api_exception
    async def get_current_user(self, request):
        """
        Get current authenticated user information.
        """
        return request.auth

    @route.get("/auth/github/url")
    @handle_api_exception
    async def get_github_auth_url(self, request):
        """
        Get GitHub OAuth authorization URL

        When called from OpenAPI docs or with 'format=json' query param:
        - Returns JSON with auth_url and state

        When called from browser/client:
        - Redirects directly to GitHub OAuth page
        """
        github_service = GitHubOAuthService()
        auth_data = github_service.get_auth_url()

        # # Check if request is from OpenAPI docs or wants JSON response
        # accept_header = request.headers.get("Accept", "")
        # format_param = request.GET.get("format", "")
        # referer = request.headers.get("Referer", "")

        # # Return JSON if:
        # # 1. Explicitly requesting JSON format
        # # 2. Accept header prefers JSON
        # # 3. Request is from OpenAPI docs/swagger UI
        # is_docs_request = (
        #     format_param == "json"
        #     or "application/json" in accept_header
        #     or "/docs" in referer
        #     or "/api/docs" in referer
        #     or "swagger" in referer.lower()
        # )

        # if is_docs_request:
        #     return JsonResponse(auth_data)

        # Otherwise redirect to GitHub OAuth
        return HttpResponseRedirect(auth_data["auth_url"])

    @route.get("/auth/github/callback", response=LoginResponseSchema)
    @handle_api_exception
    async def github_callback(self, request, code, state):
        """
        Exchange GitHub authorization code for user authentication
        """
        github_service = GitHubOAuthService()

        # Exchange code for token data (includes access_token, refresh_token, etc.)
        token_data = await github_service.exchange_code_for_token(
            code=code, state=state
        )

        if not token_data or not token_data.get("access_token"):
            raise BadRequestException("Failed to exchange GitHub code for token")

        # Get user info from GitHub
        github_user_info = await github_service.get_user_info(token_data["access_token"])
        if not github_user_info:
            raise BadRequestException("Failed to get user info from GitHub")

        # Create or update user and store GitHub tokens
        user = await github_service.create_or_update_user(github_user_info, token_data)

        # Generate JWT tokens using ninja-jwt
        refresh = RefreshToken.for_user(user)
        jwt_access_token = str(refresh.access_token)
        jwt_refresh_token = str(refresh)

        return LoginResponseSchema(
            success=True,
            message="Successfully logged in with GitHub",
            user=UserSchema.model_validate(user),
            access_token=jwt_access_token,
            refresh_token=jwt_refresh_token,
        )

    @route.post("/auth/refresh")
    @handle_api_exception
    async def refresh_token(self, request, refresh_token: str):
        """
        Refresh JWT access token using refresh token
        """
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return {
                "success": True,
                "access_token": access_token,
                "message": "Token refreshed successfully",
            }
        except Exception:
            raise UnauthorizedException("Invalid refresh token")

    # TODO: Add more endpoints:
    # @route.post("/register")
    # def register(self, request, payload: UserCreateSchema):
    #     """Register new user"""
    #     pass

    # @route.post("/login")
    # def login(self, request, payload: LoginSchema):
    #     """User login"""
    #     pass

    # @route.post("/logout", auth=django_auth)
    # def logout(self, request):
    #     """User logout"""
    #     pass

    # @route.put("/profile", auth=django_auth)
    # def update_profile(self, request, payload: UserUpdateSchema):
    #     """Update user profile"""
    #     pass
