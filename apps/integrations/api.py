from ninja_extra import ControllerBase, api_controller, route
from ninja_jwt.authentication import AsyncJWTAuth
from typing import List

from apps.core.exceptions import (
    handle_api_exception,
    UnauthorizedException,
    BadRequestException,
)
from apps.accounts.services import GitHubOAuthService
from .schemas import (
    GitHubRepoListResponse,
    GitHubOrgListResponse,
    GitHubBranchListResponse,
    GitHubTokenStatusSchema,
)
from .services import GitHubIntegrationService


@api_controller("/integrations", tags=["Integrations"])
class IntegrationsController(ControllerBase):

    def __init__(self):
        super().__init__()
        self.oauth_service = GitHubOAuthService()
        self.github_service = GitHubIntegrationService()

    # GitHub Integration Endpoints

    @route.get(
        "/github/token-status", response=GitHubTokenStatusSchema, auth=AsyncJWTAuth()
    )
    @handle_api_exception
    async def get_github_token_status(self, request):
        """
        Check GitHub token status for authenticated user

        Returns information about whether user has connected GitHub
        and if their token is still valid
        """
        user = request.auth

        return GitHubTokenStatusSchema(
            has_token=bool(user.github_access_token),
            is_expired=(
                user.is_github_token_expired() if user.github_access_token else True
            ),
            expires_at=user.github_token_expires_at,
            scopes=user.github_token_scope,
        )

    @route.get("/github/repos", response=GitHubRepoListResponse, auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_github_repos(self, request):
        """
        List GitHub repositories for authenticated user

        Requires user to have connected their GitHub account via OAuth
        Automatically refreshes token if expired
        """
        user = request.auth

        # Ensure valid token (refresh if needed)
        access_token = await self.oauth_service.ensure_valid_token(user)
        if not access_token:
            raise UnauthorizedException(
                "GitHub account not connected or token expired. Please reconnect your GitHub account.",
                details={"action": "reconnect", "url": "/api/accounts/auth/github/url"},
            )

        # Fetch repositories
        repos = await self.github_service.get_user_repos(access_token)
        if repos is None:
            raise BadRequestException("Failed to fetch repositories from GitHub")

        return GitHubRepoListResponse(success=True, repos=repos, count=len(repos))

    @route.get(
        "/github/organizations", response=GitHubOrgListResponse, auth=AsyncJWTAuth()
    )
    @handle_api_exception
    async def list_github_organizations(self, request):
        """
        List GitHub organizations for authenticated user

        Requires user to have connected their GitHub account via OAuth
        Automatically refreshes token if expired
        """
        user = request.auth

        # Ensure valid token (refresh if needed)
        access_token = await self.oauth_service.ensure_valid_token(user)
        if not access_token:
            raise UnauthorizedException(
                "GitHub account not connected or token expired. Please reconnect your GitHub account.",
                details={"action": "reconnect", "url": "/api/accounts/auth/github/url"},
            )

        # Fetch organizations
        orgs = await self.github_service.get_user_organizations(access_token)
        if orgs is None:
            raise BadRequestException("Failed to fetch organizations from GitHub")

        return GitHubOrgListResponse(success=True, organizations=orgs, count=len(orgs))

    @route.get(
        "/github/repos/{owner}/{repo}/branches",
        response=GitHubBranchListResponse,
        auth=AsyncJWTAuth(),
    )
    @handle_api_exception
    async def list_repo_branches(self, request, owner: str, repo: str):
        """
        List branches for a specific GitHub repository

        Args:
            owner: Repository owner (username or organization)
            repo: Repository name

        Requires user to have connected their GitHub account via OAuth
        Automatically refreshes token if expired
        """
        user = request.auth

        # Ensure valid token (refresh if needed)
        access_token = await self.oauth_service.ensure_valid_token(user)
        if not access_token:
            raise UnauthorizedException(
                "GitHub account not connected or token expired. Please reconnect your GitHub account.",
                details={"action": "reconnect", "url": "/api/accounts/auth/github/url"},
            )

        # Fetch branches
        branches = await self.github_service.get_repo_branches(
            access_token, owner, repo
        )
        if branches is None:
            raise BadRequestException(
                f"Failed to fetch branches for {owner}/{repo}",
                details={"owner": owner, "repo": repo},
            )

        return GitHubBranchListResponse(
            success=True,
            branches=branches,
            count=len(branches),
            repository=f"{owner}/{repo}",
        )
