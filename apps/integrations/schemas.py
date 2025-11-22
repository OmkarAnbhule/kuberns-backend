"""
Schemas for GitHub integration endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class GithubRepoOwnerSchema(BaseModel):
    """GitHub repository owner schema"""
    login: str
    id: int
    avatar_url: str
    html_url: str
    
    class Config:
        from_attributes = True

class GitHubRepoSchema(BaseModel):
    """GitHub repository schema"""
    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    owner: GithubRepoOwnerSchema
    description: Optional[str] = None
    fork: bool
    created_at: str
    updated_at: str
    pushed_at: Optional[str] = None
    size: int
    stargazers_count: int
    watchers_count: int
    language: Optional[str] = None
    forks_count: int
    open_issues_count: int
    default_branch: str
    
    class Config:
        from_attributes = True


class GitHubRepoListResponse(BaseModel):
    """Response for listing repositories"""
    success: bool = True
    repos: List[GitHubRepoSchema]
    count: int


class GitHubOrgSchema(BaseModel):
    """GitHub organization schema"""
    id: int
    login: str
    url: str
    avatar_url: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class GitHubOrgListResponse(BaseModel):
    """Response for listing organizations"""
    success: bool = True
    organizations: List[GitHubOrgSchema]
    count: int


class GitHubBranchSchema(BaseModel):
    """GitHub branch schema"""
    name: str
    protected: bool
    
    class Config:
        from_attributes = True


class GitHubBranchListResponse(BaseModel):
    """Response for listing branches"""
    success: bool = True
    branches: List[GitHubBranchSchema]
    count: int
    repository: str


class GitHubTokenStatusSchema(BaseModel):
    """GitHub token status"""
    has_token: bool
    is_expired: bool
    expires_at: Optional[datetime] = None
    scopes: Optional[str] = None
