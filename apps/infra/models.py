from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


class AWSCredential(models.Model):
    """Stores AWS credentials for users (encrypted)"""
    
    CREDENTIAL_TYPE_CHOICES = [
        ('demo', 'Demo Credentials'),
        ('user', 'User Credentials'),
    ]
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='aws_credentials')
    name = models.CharField(max_length=100, help_text="Friendly name for this credential set")
    credential_type = models.CharField(max_length=10, choices=CREDENTIAL_TYPE_CHOICES, default='user')
    
    # Encrypted fields for security
    aws_access_key = EncryptedCharField(max_length=255)
    aws_secret_key = EncryptedCharField(max_length=255)
    region = models.CharField(max_length=50, default='us-east-1')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['user', 'name']]
    
    def __str__(self):
        user_identifier = getattr(self.user, 'email', getattr(self.user, 'username', self.user.id))
        return f"{self.name} ({self.credential_type}) - {user_identifier}"


class Instance(models.Model):
    """AWS EC2 instance model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('stopping', 'Stopping'),
        ('stopped', 'Stopped'),
        ('terminated', 'Terminated'),
        ('failed', 'Failed'),
    ]
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='instances')
    instance_id = models.CharField(max_length=20, unique=True, null=True, blank=True)  # AWS instance ID
    public_ip = models.GenericIPAddressField(null=True, blank=True)
    private_ip = models.GenericIPAddressField(null=True, blank=True)
    cpu = models.IntegerField(null=True, blank=True)
    ram_mb = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Track which credentials were used
    credential = models.ForeignKey(AWSCredential, on_delete=models.SET_NULL, null=True, blank=True, related_name='instances')
    credential_type = models.CharField(max_length=10, default='demo', help_text="Type of credential used")
    
    # Instance configuration
    instance_type = models.CharField(max_length=50, default='t3.micro')
    ami_id = models.CharField(max_length=50, null=True, blank=True)
    region = models.CharField(max_length=50, default='us-east-1')
    port = models.IntegerField(null=True, blank=True, help_text="Application port")
    security_group_id = models.CharField(max_length=50, null=True, blank=True, help_text="AWS Security Group ID for cleanup")
    
    # Error tracking
    error_message = models.TextField(null=True, blank=True)
    
    # Auto-termination for demo instances (5 minutes)
    auto_terminate_at = models.DateTimeField(null=True, blank=True, help_text="When to auto-terminate this instance")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.instance_id or 'Pending'} ({self.project.name})"


class DeploymentLog(models.Model):
    """Deployment and provisioning logs"""
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='deployment_logs')
    instance = models.ForeignKey(Instance, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    output = models.TextField()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.project.name} - {self.status} at {self.timestamp}"