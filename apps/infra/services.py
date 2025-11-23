"""
Service layer for infrastructure management.
Handles credential management, instance provisioning, and status tracking.
"""

import os
import logging
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.db import transaction
from asgiref.sync import sync_to_async

from .models import AWSCredential, Instance, DeploymentLog
from .utils.aws_provision import provision_ec2_instance, get_instance_status
from apps.projects.models import Project

logger = logging.getLogger(__name__)


class CredentialService:
    """Service for managing AWS credentials"""
    
    @staticmethod
    def get_demo_credentials() -> Tuple[str, str, str]:
        """
        Get demo/platform AWS credentials from environment variables.
        
        Returns:
            Tuple of (access_key, secret_key, region)
        
        Raises:
            Exception: If demo credentials are not configured
        """
        access_key = os.getenv('AWS_DEMO_ACCESS_KEY')
        secret_key = os.getenv('AWS_DEMO_SECRET_KEY')
        region = os.getenv('AWS_DEMO_REGION', 'us-east-1')
        
        if not access_key or not secret_key:
            raise Exception(
                "Demo AWS credentials not configured. "
                "Please set AWS_DEMO_ACCESS_KEY and AWS_DEMO_SECRET_KEY environment variables."
            )
        
        return access_key, secret_key, region
    
    @staticmethod
    async def save_user_credentials(
        user,
        name: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = 'us-east-1'
    ) -> AWSCredential:
        """
        Save user's AWS credentials (encrypted) to database.
        
        Args:
            user: User instance
            name: Friendly name for credentials
            aws_access_key: AWS access key
            aws_secret_key: AWS secret key
            region: AWS region
        
        Returns:
            AWSCredential instance
        """
        credential = await sync_to_async(AWSCredential.objects.create)(
            user=user,
            name=name,
            credential_type='user',
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            region=region
        )
        
        logger.info(f"Saved AWS credentials for user {user.email}: {name}")
        return credential
    
    @staticmethod
    async def get_user_credentials(user, credential_id: int) -> Optional[AWSCredential]:
        """Get user's saved credentials by ID"""
        try:
            return await sync_to_async(
                AWSCredential.objects.get
            )(id=credential_id, user=user, is_active=True)
        except AWSCredential.DoesNotExist:
            return None


class InstanceService:
    """Service for managing EC2 instances"""
    
    @staticmethod
    async def create_instance(
        user,
        project_id: str,
        credential_mode: str,
        region: str,
        port: int = 80,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None
    ) -> Dict:
        """
        Create a minimal EC2 instance.
        
        Uses hardcoded minimal configuration:
        - Instance Type: t3.micro (2 vCPU, 1GB RAM)
        - Disk Size: 8 GB
        - AMI: Ubuntu 22.04 LTS (region-specific)
        
        Args:
            user: User instance
            project_id: Project UUID
            credential_mode: 'demo' or 'user'
            region: AWS region
            port: Single application port to open
            aws_access_key: User's AWS access key (if credential_mode='user')
            aws_secret_key: User's AWS secret key (if credential_mode='user')
        
        Returns:
            Dict with instance details and status
        """
        
        # Get project
        try:
            project = await sync_to_async(Project.objects.get)(id=project_id, owner=user)
        except Project.DoesNotExist:
            raise Exception(f"Project {project_id} not found or you don't have access")
        
        # Get credentials based on mode
        if credential_mode == 'demo':
            access_key, secret_key, default_region = CredentialService.get_demo_credentials()
            region = region or default_region
            credential = None
        else:
            if not aws_access_key or not aws_secret_key:
                raise Exception("AWS credentials required when using 'user' credential mode")
            
            access_key = aws_access_key
            secret_key = aws_secret_key
            credential = None  # Could save it if needed
        
        # Calculate auto-termination time for demo instances (5 minutes)
        from django.utils import timezone
        from datetime import timedelta
        auto_terminate_at = None
        if credential_mode == 'demo':
            auto_terminate_at = timezone.now() + timedelta(minutes=5)
        
        # Create instance record with hardcoded defaults
        instance = await sync_to_async(Instance.objects.create)(
            project=project,
            credential=credential,
            credential_type=credential_mode,
            status='pending',
            instance_type='t3.micro',  # Hardcoded
            region=region,
            port=port,  # Store the port
            auto_terminate_at=auto_terminate_at
        )
        
        # Create initial deployment log
        log_output = f'Starting EC2 instance provisioning in {region}...'
        if credential_mode == 'demo':
            log_output += f'\n⚠️  DEMO MODE: Instance will auto-terminate in 5 minutes at {auto_terminate_at.strftime("%Y-%m-%d %H:%M:%S UTC")}'
        
        log = await sync_to_async(DeploymentLog.objects.create)(
            project=project,
            instance=instance,
            status='started',
            output=log_output
        )
        
        try:
            # Provision EC2 instance
            logger.info(f"Provisioning EC2 instance for project {project.name}")
            
            result = await sync_to_async(provision_ec2_instance)(
                aws_access_key=access_key,
                aws_secret_key=secret_key,
                region=region,
                project_name=project.name,
                port=port
            )
            
            # Update instance with AWS details
            instance.instance_id = result['instance_id']
            instance.public_ip = result.get('public_ip')
            instance.private_ip = result.get('private_ip')
            instance.status = result['status']
            instance.ami_id = result.get('ami_id')
            await sync_to_async(instance.save)()
            
            # Construct instance URL
            public_ip = result.get('public_ip')
            instance_url = None
            if public_ip:
                # URL format: http://ip:port
                instance_url = f"http://{public_ip}:{port}"
            
            # Update deployment log
            log.status = 'completed'
            log.output += f"\n\nInstance {result['instance_id']} created successfully!"
            log.output += f"\nPublic IP: {public_ip or 'Pending'}"
            log.output += f"\nStatus: {result['status']}"
            if instance_url:
                log.output += f"\n\n🌐 Access your instance at: {instance_url}"
                log.output += f"\n\n⏳ Note: Please wait 1-2 minutes for the web server to finish installing and starting."
            if credential_mode == 'demo':
                log.output += f"\n\n⚠️  This is a DEMO instance - it will automatically terminate in 5 minutes"
            await sync_to_async(log.save)()
            
            logger.info(f"Successfully provisioned instance {result['instance_id']}")
            
            return {
                'success': True,
                'instance_id': instance.id,
                'aws_instance_id': result['instance_id'],
                'url': instance_url,
                'public_ip': public_ip,
                'port': port,
                'message': 'Instance created successfully',
                'deployment_log_id': log.id
            }
        
        except Exception as e:
            logger.error(f"Error provisioning instance: {str(e)}")
            
            # Update instance status
            instance.status = 'failed'
            instance.error_message = str(e)
            await sync_to_async(instance.save)()
            
            # Update deployment log
            log.status = 'failed'
            log.output += f"\n\nError: {str(e)}"
            await sync_to_async(log.save)()
            
            return {
                'success': False,
                'instance_id': instance.id,
                'message': f'Instance creation failed: {str(e)}',
                'deployment_log_id': log.id
            }
    
    @staticmethod
    async def get_instance_deployment_status(instance_id: int, user) -> Dict:
        """
        Get detailed deployment status of an instance.
        
        Args:
            instance_id: Database instance ID
            user: User instance
        
        Returns:
            Dict with instance details and deployment logs
        """
        try:
            # Get instance
            instance = await sync_to_async(
                Instance.objects.select_related('project', 'credential').get
            )(id=instance_id, project__owner=user)
            
            # Get deployment logs
            logs = await sync_to_async(list)(
                instance.logs.all().order_by('-timestamp')[:10]
            )
            
            # If instance has AWS ID, try to get live status
            if instance.instance_id and instance.credential_type == 'demo':
                try:
                    access_key, secret_key, _ = CredentialService.get_demo_credentials()
                    
                    live_status = await sync_to_async(get_instance_status)(
                        aws_access_key=access_key,
                        aws_secret_key=secret_key,
                        region=instance.region,
                        instance_id=instance.instance_id
                    )
                    
                    # Update instance if status changed
                    if live_status['status'] != instance.status:
                        instance.status = live_status['status']
                        instance.public_ip = live_status.get('public_ip')
                        instance.private_ip = live_status.get('private_ip')
                        await sync_to_async(instance.save)()
                
                except Exception as e:
                    logger.warning(f"Could not fetch live status: {str(e)}")
            
            return {
                'instance': instance,
                'logs': logs
            }
        
        except Instance.DoesNotExist:
            raise Exception(f"Instance {instance_id} not found or you don't have access")

