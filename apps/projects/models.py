import uuid
from django.db import models
from django.conf import settings
from encrypted_model_fields.fields import EncryptedTextField


class Template(models.Model):
    """Project template model"""

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, null=True, blank=True)
    slug = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Plan(models.Model):
    """Pricing plan model"""

    name = models.CharField(max_length=50)
    cpu_cores = models.IntegerField(default=0)
    ram_mb = models.IntegerField(default=0)
    bandwidth_gb = models.IntegerField(default=0)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_hourly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    storage_gb = models.IntegerField(default=0)
    description = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"


class Project(models.Model):
    """Main project model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    aws_region = models.CharField(max_length=20)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    organization = models.CharField(max_length=255)
    repository_name = models.CharField(max_length=255)
    branch_name = models.CharField(max_length=255)
    selected_port = models.IntegerField(null=True, blank=True)
    is_random_port = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class DatabaseConfig(models.Model):
    """Database configuration for projects"""

    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    connection_url_encrypted = EncryptedTextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"DB Config for {self.project.name}"


class EnvVar(models.Model):
    """Environment variables for projects"""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="env_vars"
    )
    key = models.CharField(max_length=100)
    value_encrypted = EncryptedTextField()
    is_secret = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["project", "key"]

    def __str__(self):
        return f"{self.project.name}:{self.key}"
