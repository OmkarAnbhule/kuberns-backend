"""
GitHub integration service for repository and organization management
"""

import httpx
from typing import Optional, List, Dict
from django.contrib.auth import get_user_model

User = get_user_model()


class GitHubIntegrationService:
    """Service for GitHub repository and organization operations"""

    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_USER_URL = f"{GITHUB_API_BASE}/user"
    GITHUB_REPOS_URL = f"{GITHUB_API_BASE}/user/repos"
    GITHUB_ORGS_URL = f"{GITHUB_API_BASE}/user/orgs"

    def __init__(self):
        self.headers_base = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Kuberns-App",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Get headers with authorization token"""
        headers = self.headers_base.copy()
        headers["Authorization"] = f"Bearer {access_token}"
        return headers

    async def get_user_repos(
        self, 
        access_token: str, 
        per_page: int = 100,
        sort: str = "updated"
    ) -> Optional[List[Dict]]:
        """
        Get user's GitHub repositories

        Args:
            access_token: GitHub access token
            per_page: Number of repos per page (max 100)
            sort: Sort order (created, updated, pushed, full_name)

        Returns:
            List of repositories or None if failed
        """
        headers = self._get_headers(access_token)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GITHUB_REPOS_URL,
                    headers=headers,
                    params={"per_page": per_page, "sort": sort}
                )
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"GitHub repos request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            return None

    async def get_user_organizations(self, access_token: str) -> Optional[List[Dict]]:
        """
        Get user's GitHub organizations

        Args:
            access_token: GitHub access token

        Returns:
            List of organizations or None if failed
        """
        headers = self._get_headers(access_token)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.GITHUB_ORGS_URL, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"GitHub orgs request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            return None

    async def get_repo_branches(
        self, 
        access_token: str, 
        owner: str, 
        repo: str,
        per_page: int = 100
    ) -> Optional[List[Dict]]:
        """
        Get branches for a specific repository

        Args:
            access_token: GitHub access token
            owner: Repository owner
            repo: Repository name
            per_page: Number of branches per page (max 100)

        Returns:
            List of branches or None if failed
        """
        headers = self._get_headers(access_token)
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/branches"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers=headers,
                    params={"per_page": per_page}
                )
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"GitHub branches request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            return None

    async def get_repo_details(
        self, 
        access_token: str, 
        owner: str, 
        repo: str
    ) -> Optional[Dict]:
        """
        Get detailed information about a specific repository

        Args:
            access_token: GitHub access token
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository details or None if failed
        """
        headers = self._get_headers(access_token)
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"GitHub repo details request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            return None

    async def get_org_repos(
        self, 
        access_token: str, 
        org: str,
        per_page: int = 100
    ) -> Optional[List[Dict]]:
        """
        Get repositories for a specific organization

        Args:
            access_token: GitHub access token
            org: Organization name
            per_page: Number of repos per page (max 100)

        Returns:
            List of repositories or None if failed
        """
        headers = self._get_headers(access_token)
        url = f"{self.GITHUB_API_BASE}/orgs/{org}/repos"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    headers=headers,
                    params={"per_page": per_page}
                )
                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            print(f"GitHub org repos request failed: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            return None
