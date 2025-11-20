from django.db import models


class Instance(models.Model):
    """AWS EC2 instance model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('stopping', 'Stopping'),
        ('stopped', 'Stopped'),
        ('terminated', 'Terminated'),
    ]
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='instances')
    instance_id = models.CharField(max_length=20, unique=True)  # AWS instance ID
    public_ip = models.GenericIPAddressField(null=True, blank=True)
    cpu = models.IntegerField()
    ram_mb = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.instance_id} ({self.project.name})"


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