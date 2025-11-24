"""
Management command to terminate expired demo instances.

Run this periodically via cron:
    */5 * * * * cd /path/to/project && python manage.py terminate_expired_instances

Or run manually:
    python manage.py terminate_expired_instances
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.infra.models import Instance, DeploymentLog
from apps.infra.utils.aws_provision import terminate_instance
from apps.infra.services import CredentialService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Terminate demo instances that have exceeded their 5-minute lifetime'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be terminated without actually terminating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No instances will be terminated'))
        
        # Find all demo instances that need to be terminated
        now = timezone.now()
        expired_instances = Instance.objects.filter(
            credential_type='demo',
            auto_terminate_at__lte=now,
            status__in=['pending', 'running']
        ).select_related('project')
        
        count = expired_instances.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired instances found'))
            return
        
        self.stdout.write(f'Found {count} expired demo instance(s) to terminate')
        
        # Get demo credentials for termination
        try:
            access_key, secret_key, _ = CredentialService.get_demo_credentials()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to get demo credentials: {str(e)}'))
            return
        
        terminated_count = 0
        failed_count = 0
        
        for instance in expired_instances:
            try:
                self.stdout.write(f'Processing instance {instance.instance_id} (project: {instance.project.name})')
                
                if not instance.instance_id:
                    self.stdout.write(self.style.WARNING(f'  Skipping - no AWS instance ID'))
                    instance.status = 'failed'
                    instance.error_message = 'No AWS instance ID to terminate'
                    if not dry_run:
                        instance.save()
                    continue
                
                if dry_run:
                    self.stdout.write(self.style.WARNING(f'  Would terminate {instance.instance_id}'))
                    continue
                
                # Terminate the instance and clean up security group
                terminate_instance(
                    aws_access_key=access_key,
                    aws_secret_key=secret_key,
                    region=instance.region,
                    instance_id=instance.instance_id,
                    security_group_id=instance.security_group_id  # Pass for cleanup
                )
                
                # Update instance status
                instance.status = 'terminated'
                instance.save()
                
                # Create deployment log
                DeploymentLog.objects.create(
                    project=instance.project,
                    instance=instance,
                    status='completed',
                    output=f'Instance {instance.instance_id} auto-terminated after 5 minutes (demo mode)'
                )
                
                terminated_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Terminated {instance.instance_id}'))
                
            except Exception as e:
                failed_count += 1
                error_msg = f'Failed to terminate instance {instance.instance_id}: {str(e)}'
                self.stdout.write(self.style.ERROR(f'  ✗ {error_msg}'))
                logger.error(error_msg)
                
                # Update instance with error
                if not dry_run:
                    instance.status = 'failed'
                    instance.error_message = str(e)
                    instance.save()
                    
                    DeploymentLog.objects.create(
                        project=instance.project,
                        instance=instance,
                        status='failed',
                        output=f'Failed to auto-terminate: {str(e)}'
                    )
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'\nDRY RUN: Would have terminated {count} instance(s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully terminated: {terminated_count}'))
            if failed_count > 0:
                self.stdout.write(self.style.ERROR(f'Failed: {failed_count}'))

