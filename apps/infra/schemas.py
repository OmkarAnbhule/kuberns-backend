from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProvisionRequest(BaseModel):
    """
    Request schema for provisioning infrastructure.
    
    TODO: Add validation for AWS credentials and instance configuration
    Note: AWS credentials should NOT be stored - use temporary credentials or IAM roles
    """
    project_id: UUID
    aws_access_key: str  # TODO: Use temporary credentials or IAM roles instead
    aws_secret_key: str  # TODO: Use temporary credentials or IAM roles instead
    region: str
    instance_type: str = "t3.micro"
    ami_id: Optional[str] = None  # Will use default if not provided
    key_name: Optional[str] = None  # SSH key pair name


class ProvisionResponse(BaseModel):
    """Response schema for provisioning requests"""
    success: bool
    instance_id: Optional[str] = None
    message: str
    deployment_log_id: Optional[int] = None


class InstanceSchema(BaseModel):
    """Instance response schema"""
    id: int
    instance_id: str
    public_ip: Optional[str]
    cpu: int
    ram_mb: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeploymentLogSchema(BaseModel):
    """Deployment log response schema"""
    id: int
    status: str
    output: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class DeployRequest(BaseModel):
    """Application deployment request schema"""
    project_id: UUID
    # TODO: Add deployment configuration fields