from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GitHubRepoSchema(BaseModel):
    """GitHub repository response schema"""
    id: int
    organization: str
    repo_name: str
    branch: str
    github_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GitHubRepoCreateSchema(BaseModel):
    """GitHub repository creation schema"""
    organization: str
    repo_name: str
    branch: str = "main"
    github_id: int


class GitHubWebhookSchema(BaseModel):
    """GitHub webhook payload schema"""
    action: str
    repository: dict
    # TODO: Add more webhook fields as needed