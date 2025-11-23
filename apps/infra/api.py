from ninja_extra import ControllerBase, api_controller, route
from typing import List
from asgiref.sync import sync_to_async
from ninja_jwt.authentication import AsyncJWTAuth

from apps.core.exceptions import handle_api_exception
from .schemas import (
    CreateInstanceRequest, 
    CreateInstanceResponse, 
    DeploymentStatusResponse,
    InstanceSchema, 
    DeploymentLogSchema,
    AWSCredentialSchema,
    CreateAWSCredentialRequest
)
from .services import InstanceService, CredentialService
from .models import Instance


@api_controller("/infra", tags=["Infrastructure"])
class InfraController(ControllerBase):
    
    @route.post("/instances/create", response=CreateInstanceResponse, auth=AsyncJWTAuth())
    @handle_api_exception
    async def create_instance(self, request, payload: CreateInstanceRequest):
        """
        Create a new AWS EC2 instance.
        
        Supports two credential modes:
        1. 'demo': Uses platform/demo AWS credentials (configured in environment)
        2. 'user': Uses user-provided AWS credentials
        
        Example request for demo mode:
        {
            "project_id": "uuid-here",
            "credential_mode": "demo",
            "region": "us-east-1",
            "port": 80
        }
        
        Example request for user mode:
        {
            "project_id": "uuid-here",
            "credential_mode": "user",
            "aws_access_key": "YOUR_ACCESS_KEY",
            "aws_secret_key": "YOUR_SECRET_KEY",
            "region": "us-west-2",
            "port": 8080
        }
        """
        
        result = await InstanceService.create_instance(
            user=request.user,
            project_id=str(payload.project_id),
            credential_mode=payload.credential_mode,
            region=payload.region,
            port=payload.port,
            aws_access_key=payload.aws_access_key,
            aws_secret_key=payload.aws_secret_key
        )
        
        return CreateInstanceResponse(
            success=result['success'],
            instance_id=result.get('instance_id'),
            aws_instance_id=result.get('aws_instance_id'),
            url=result.get('url'),
            public_ip=result.get('public_ip'),
            port=result.get('port'),
            message=result['message'],
            deployment_log_id=result.get('deployment_log_id')
        )
    
    @route.get("/instances/{instance_id}/status", response=DeploymentStatusResponse, auth=AsyncJWTAuth())
    @handle_api_exception
    async def get_deployment_status(self, request, instance_id: int):
        """
        Get the deployment status and details of an EC2 instance.
        
        Returns:
        - Instance information (ID, IP addresses, status, etc.)
        - Deployment logs
        - Live AWS status (if using demo credentials)
        
        Example response:
        {
            "instance_id": 1,
            "aws_instance_id": "i-0123456789abcdef",
            "status": "running",
            "public_ip": "54.123.45.67",
            "private_ip": "172.31.1.1",
            "instance_type": "t3.micro",
            "region": "us-east-1",
            "credential_type": "demo",
            "created_at": "2025-01-01T00:00:00Z",
            "logs": [...]
        }
        """
        
        result = await InstanceService.get_instance_deployment_status(
            instance_id=instance_id,
            user=request.user
        )
        
        instance = result['instance']
        logs = result['logs']
        
        # Construct URL from public IP and port
        instance_url = None
        if instance.public_ip and instance.port:
            instance_url = f"http://{instance.public_ip}:{instance.port}"
        
        return DeploymentStatusResponse(
            instance_id=instance.id,
            aws_instance_id=instance.instance_id,
            status=instance.status,
            url=instance_url,
            public_ip=instance.public_ip,
            private_ip=instance.private_ip,
            instance_type=instance.instance_type,
            region=instance.region,
            credential_type=instance.credential_type,
            error_message=instance.error_message,
            created_at=instance.created_at,
            updated_at=instance.updated_at,
            auto_terminate_at=instance.auto_terminate_at,
            logs=[DeploymentLogSchema(
                id=log.id,
                status=log.status,
                output=log.output,
                timestamp=log.timestamp
            ) for log in logs]
        )
    
    @route.get("/instances", response=List[InstanceSchema], auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_instances(self, request):
        """
        List all EC2 instances for the authenticated user.
        
        Returns instances across all user's projects.
        """
        
        instances = await sync_to_async(list)(
            Instance.objects.filter(project__owner=request.user)
            .select_related('project')
            .order_by('-created_at')
        )
        
        # Build response with computed URLs
        result = []
        for instance in instances:
            instance_data = InstanceSchema.from_orm(instance)
            # Compute URL from public_ip and port
            if instance.public_ip and instance.port:
                instance_data.url = f"http://{instance.public_ip}:{instance.port}"
            result.append(instance_data)
        
        return result
    
    @route.post("/credentials", response=AWSCredentialSchema, auth=AsyncJWTAuth())
    @handle_api_exception
    async def save_aws_credentials(self, request, payload: CreateAWSCredentialRequest):
        """
        Save AWS credentials for the authenticated user (encrypted).
        
        These credentials can be reused for multiple deployments.
        All credentials are encrypted at rest using django-encrypted-model-fields.
        
        Example request:
        {
            "name": "My AWS Account",
            "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-east-1"
        }
        """
        
        credential = await CredentialService.save_user_credentials(
            user=request.user,
            name=payload.name,
            aws_access_key=payload.aws_access_key,
            aws_secret_key=payload.aws_secret_key,
            region=payload.region
        )
        
        return AWSCredentialSchema.from_orm(credential)
    