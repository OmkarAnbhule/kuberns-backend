from pydantic import BaseModel
from ninja import ModelSchema
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from .models import Project

class TemplateSchema(BaseModel):
    id: int
    name: str
    category: str
    slug: Optional[str]

    class Config:
        from_attributes = True


class PlanSchema(BaseModel):
    id: int
    name: str
    cpu_cores: int
    ram_mb: int
    bandwidth_gb: int
    price_monthly: float
    price_hourly: float
    storage_gb: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


class EnvVarCreate(BaseModel):
    key: str
    value: str
    is_secret: bool = False


class EnvVarSchema(BaseModel):
    id: int
    key: str
    is_secret:bool=False
    # Note: Don't expose encrypted values in API responses

    class Config:
        from_attributes = True


class DatabaseConfigCreate(BaseModel):
    connection_url: str  # Will be encrypted before storage


class ProjectCreate(BaseModel):
    """
    Schema for creating new projects.

    TODO: Add validation for:
    - AWS region format
    - Port ranges
    - Template/Plan existence
    """

    name: str
    organization: str
    repository_name: str
    branch_name: str
    aws_region: str
    template_id: int
    plan_id: int
    github_repo_id: Optional[int] = None
    selected_port: Optional[int] = None
    is_random_port: bool = False
    env_vars: List[EnvVarCreate] = []
    database_config: Optional[DatabaseConfigCreate] = None


class ProjectRead(ModelSchema):
    """
    Schema for reading project data.

    TODO: Add nested serialization for related objects
    """
    plan: PlanSchema
    template: TemplateSchema
    env_vars: Optional[List[EnvVarSchema]] = None

    class Config:
        model = Project
        model_fields = "__all__"
        from_attributes = True
        
class CreateProjectResponse(BaseModel):
    """
    Schema for reading project data.

    TODO: Add nested serialization for related objects
    """

    id: UUID
    name: str
    organization: str
    repository_name: str
    branch_name: str
    aws_region: str
    selected_port: Optional[int]
    is_random_port: bool
    created_at: datetime
    updated_at: datetime
    template: TemplateSchema
    plan: PlanSchema

    class Config:
        from_attributes = True
