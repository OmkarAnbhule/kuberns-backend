from ninja_extra import ControllerBase, api_controller, route
from typing import List

from .schemas import GitHubRepoSchema, GitHubRepoCreateSchema, GitHubWebhookSchema


@api_controller("/integrations", tags=["Integrations"])
class IntegrationsController(ControllerBase):
    
    # TODO: Add endpoints:
    # @route.get("/repos", response=List[GitHubRepoSchema])
    # def list_repos(self, request):
    #     """List connected GitHub repositories"""
    #     pass
    
    # @route.post("/repos", response=GitHubRepoSchema)
    # def connect_repo(self, request, payload: GitHubRepoCreateSchema):
    #     """Connect new GitHub repository"""
    #     pass
    
    # @route.delete("/repos/{repo_id}")
    # def disconnect_repo(self, request, repo_id: int):
    #     """Disconnect GitHub repository"""
    #     pass
    
    # @route.post("/webhook/github")
    # def github_webhook(self, request):
    #     """Handle GitHub webhook events"""
    #     pass
    
    pass  # Placeholder for empty controller