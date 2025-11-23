from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime


class CreateInstanceRequest(BaseModel):
    """
    Request schema for creating an AWS EC2 instance.
    Supports both demo credentials and user-provided credentials.
    """
    project_id: UUID
    
    # Credential configuration
    credential_mode: Literal['demo', 'user'] = Field(
        default='demo',
        description="Use 'demo' for platform credentials or 'user' for custom credentials"
    )
    
    # Optional: User-provided credentials (only when credential_mode='user')
    aws_access_key: Optional[str] = Field(None, description="AWS Access Key (required if credential_mode='user')")
    aws_secret_key: Optional[str] = Field(None, description="AWS Secret Key (required if credential_mode='user')")
    
    # Instance configuration - User provides these
    region: str = Field(default='us-east-1', description="AWS region")
    port: int = Field(default=80, description="Single application port to open (in addition to SSH port 22)")
    
    # Hardcoded defaults (not configurable by user)
    # instance_type: t3.micro (2 vCPU, 1GB RAM - smallest general purpose)
    # disk_size_gb: 8 GB (minimum allowed)
    # AMI: Auto-selected based on region (Ubuntu 22.04 LTS)
    
    @model_validator(mode='after')
    def validate_user_credentials(self):
        """Ensure credentials are provided when using user mode"""
        if self.credential_mode == 'user':
            if not self.aws_access_key:
                raise ValueError("aws_access_key is required when credential_mode is 'user'")
            if not self.aws_secret_key:
                raise ValueError("aws_secret_key is required when credential_mode is 'user'")
        return self


class CreateInstanceResponse(BaseModel):
    """Response schema for instance creation"""
    success: bool
    instance_id: Optional[int] = Field(None, description="Database instance ID")
    aws_instance_id: Optional[str] = Field(None, description="AWS EC2 instance ID")
    url: Optional[str] = Field(None, description="URL to access the deployed instance")
    public_ip: Optional[str] = Field(None, description="Public IP address")
    port: Optional[int] = Field(None, description="Application port")
    message: str
    deployment_log_id: Optional[int] = None


class DeploymentStatusResponse(BaseModel):
    """Response schema for deployment status"""
    instance_id: int
    aws_instance_id: Optional[str]
    status: str
    url: Optional[str] = Field(None, description="URL to access the instance")
    public_ip: Optional[str]
    private_ip: Optional[str]
    instance_type: str
    region: str
    credential_type: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    auto_terminate_at: Optional[datetime] = Field(None, description="When instance will auto-terminate (demo mode)")
    
    # Deployment logs
    logs: List['DeploymentLogSchema'] = []
    
    class Config:
        from_attributes = True


class InstanceSchema(BaseModel):
    """Instance response schema"""
    id: int
    instance_id: Optional[str]
    url: Optional[str] = Field(None, description="URL to access the instance")
    public_ip: Optional[str]
    private_ip: Optional[str]
    port: Optional[int]
    cpu: Optional[int]
    ram_mb: Optional[int]
    status: str
    instance_type: str
    region: str
    credential_type: str
    error_message: Optional[str]
    auto_terminate_at: Optional[datetime] = Field(None, description="When instance will auto-terminate")
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


class DeploymentLogDetailSchema(BaseModel):
    """Detailed deployment log with project and instance info"""
    id: int
    status: str
    output: str
    timestamp: datetime
    project_id: str = Field(description="Project UUID")
    project_name: str = Field(description="Project name")
    instance_id: Optional[int] = Field(None, description="Database instance ID")
    aws_instance_id: Optional[str] = Field(None, description="AWS EC2 instance ID")
    
    class Config:
        from_attributes = True


class AWSCredentialSchema(BaseModel):
    """AWS Credential response schema (without sensitive data)"""
    id: int
    name: str
    credential_type: str
    region: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateAWSCredentialRequest(BaseModel):
    """Request to save AWS credentials"""
    name: str = Field(..., description="Friendly name for this credential set")
    aws_access_key: str
    aws_secret_key: str
    region: str = Field(default='us-east-1')


# Forward reference resolution
DeploymentStatusResponse.model_rebuild()