from pydantic import BaseModel
from typing import Optional


class UserSchema(BaseModel):
    """User response schema"""
    id: int
    username: str
    display_name: str
    email: str
    github_username: Optional[str] = None
    github_avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    """User registration schema"""
    username: str
    email: str
    password: str
    display_name: Optional[str] = None


class UserUpdateSchema(BaseModel):
    """User profile update schema"""
    display_name: Optional[str] = None
    email: Optional[str] = None


class LoginSchema(BaseModel):
    """User login schema"""
    username: str
    password: str


class GitHubLoginSchema(BaseModel):
    """GitHub OAuth login schema"""
    code: str
    state: Optional[str] = None


class GitHubAuthUrlSchema(BaseModel):
    """GitHub OAuth URL response schema"""
    auth_url: str
    state: str


class LoginResponseSchema(BaseModel):
    """Login response schema"""
    success: bool
    message: str
    user: Optional[UserSchema] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class RefreshTokenSchema(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class RefreshTokenResponseSchema(BaseModel):
    """Refresh token response schema"""
    success: bool
    message: str
    access_token: Optional[str] = None