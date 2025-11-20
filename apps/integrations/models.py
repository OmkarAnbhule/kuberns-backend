from django.db import models


class GitHubRepo(models.Model):
    """
    GitHub repository integration model.
    
    TODO: Add validation for GitHub API integration
    """
    organization = models.CharField(max_length=100)
    repo_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, default='main')
    github_id = models.IntegerField(unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['organization', 'repo_name']
    
    def __str__(self):
        return f"{self.organization}/{self.repo_name}:{self.branch}"