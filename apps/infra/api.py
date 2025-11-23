from ninja_extra import ControllerBase, api_controller, route
from typing import List, Optional
from asgiref.sync import sync_to_async
from ninja_jwt.authentication import AsyncJWTAuth

from apps.core.exceptions import handle_api_exception
from .schemas import (
    CreateInstanceRequest, 
    CreateInstanceResponse, 
    DeploymentStatusResponse,
    InstanceSchema, 
    DeploymentLogSchema,
    DeploymentLogDetailSchema,
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
    
    @route.get("/instances/{instance_id}/logs", response=List[DeploymentLogSchema], auth=AsyncJWTAuth())
    @handle_api_exception
    async def get_instance_logs(self, request, instance_id: int, limit: int = 50):
        """
        Get deployment logs for a specific instance.
        
        Args:
            instance_id: Database instance ID
            limit: Number of logs to return (default: 50, max: 100)
        
        Returns:
            List of deployment logs ordered by most recent first
        
        Example response:
        [
            {
                "id": 42,
                "status": "completed",
                "output": "Instance i-xxx created successfully!...",
                "timestamp": "2025-11-23T21:00:00Z"
            },
            {
                "id": 41,
                "status": "started",
                "output": "Starting EC2 instance provisioning...",
                "timestamp": "2025-11-23T20:59:55Z"
            }
        ]
        """
        from .models import Instance, DeploymentLog
        
        # Limit max to 100
        limit = min(limit, 100)
        
        # Verify instance belongs to user
        try:
            instance = await sync_to_async(
                Instance.objects.select_related('project').get
            )(id=instance_id, project__owner=request.user)
        except Instance.DoesNotExist:
            from apps.core.exceptions import InternalServerException
            raise InternalServerException(f"Instance {instance_id} not found or you don't have access")
        
        # Get logs
        logs = await sync_to_async(list)(
            DeploymentLog.objects.filter(instance=instance)
            .order_by('-timestamp')[:limit]
        )
        
        return [DeploymentLogSchema(
            id=log.id,
            status=log.status,
            output=log.output,
            timestamp=log.timestamp
        ) for log in logs]
    
    @route.get("/instances", response=List[InstanceSchema], auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_instances(self, request, project_id: Optional[str] = None):
        """
        List all EC2 instances for the authenticated user.
        
        Args:
            project_id: Optional UUID to filter by specific project
        
        Returns:
            List of instances (all projects or filtered by project_id)
        
        Examples:
            GET /api/infra/instances
            -> Returns all instances
            
            GET /api/infra/instances?project_id=550e8400-e29b-41d4-a716-446655440000
            -> Returns instances for specific project only
        """
        from uuid import UUID
        
        # Build query
        query = Instance.objects.filter(project__owner=request.user)
        
        # Filter by project if provided
        if project_id:
            try:
                project_uuid = UUID(project_id)
                query = query.filter(project_id=project_uuid)
            except ValueError:
                from apps.core.exceptions import InternalServerException
                raise InternalServerException("Invalid project_id format. Must be a valid UUID.")
        
        instances = await sync_to_async(list)(
            query.select_related('project').order_by('-created_at')
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
    
    @route.get("/logs", response=List[DeploymentLogDetailSchema], auth=AsyncJWTAuth())
    @handle_api_exception
    async def get_all_logs(self, request, limit: int = 50):
        """
        Get all deployment logs for the authenticated user across all instances.
        
        Args:
            limit: Number of logs to return (default: 50, max: 100)
        
        Returns:
            List of all deployment logs with project and instance details
        
        Useful for:
        - Activity dashboard
        - Recent deployments view
        - Audit trail
        
        Example response:
        [
            {
                "id": 42,
                "status": "completed",
                "output": "Instance i-xxx created successfully!...",
                "timestamp": "2025-11-23T21:00:00Z",
                "project_id": "uuid",
                "project_name": "my-app",
                "instance_id": 1,
                "aws_instance_id": "i-0123456789abcdef"
            }
        ]
        """
        from .models import DeploymentLog
        
        # Limit max to 100
        limit = min(limit, 100)
        
        # Get all logs for user's instances
        logs = await sync_to_async(list)(
            DeploymentLog.objects.filter(project__owner=request.user)
            .select_related('project', 'instance')
            .order_by('-timestamp')[:limit]
        )
        
        return [DeploymentLogDetailSchema(
            id=log.id,
            status=log.status,
            output=log.output,
            timestamp=log.timestamp,
            project_id=str(log.project.id),
            project_name=log.project.name,
            instance_id=log.instance.id if log.instance else None,
            aws_instance_id=log.instance.instance_id if log.instance else None
        ) for log in logs]
    
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
    