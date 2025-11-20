from pydantic import BaseModel
from typing import Optional


class UserSchema(BaseModel):
    """User response schema"""
    id: int
    username: str
    display_name: str
    email: str
    
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


class LoginResponseSchema(BaseModel):
    """Login response schema"""
    success: bool
    message: str
    user: Optional[UserSchema] = None