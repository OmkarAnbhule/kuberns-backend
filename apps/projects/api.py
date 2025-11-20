from ninja_extra import ControllerBase, api_controller, route
from ninja.security import django_auth
from django.shortcuts import get_object_or_404
from django.db import transaction
from typing import List
from uuid import UUID

from .models import Project, Template, Plan
from .schemas import ProjectCreate, ProjectRead, TemplateSchema, PlanSchema


@api_controller("/projects", tags=["Projects"])
class ProjectsController(ControllerBase):
    
    @route.get("/", response=List[ProjectRead], auth=django_auth)
    def list_projects(self, request):
        """
        List all projects for the authenticated user.
        
        TODO: Add pagination, filtering, and sorting
        """
        projects = Project.objects.filter(owner=request.user, deleted_at__isnull=True)
        return projects

    @route.post("/", response=ProjectRead, auth=django_auth)
    def create_project(self, request, payload: ProjectCreate):
        """
        Create a new project with nested resources.
        
        TODO: Implement in transaction with proper error handling:
        - Validate template and plan exist
        - Create project
        - Create database config if provided
        - Create environment variables
        - Handle GitHub repo association
        """
        with transaction.atomic():
            # Placeholder implementation
            template = get_object_or_404(Template, id=payload.template_id)
            plan = get_object_or_404(Plan, id=payload.plan_id)
            
            project = Project.objects.create(
                owner=request.user,
                name=payload.name,
                city=payload.city,
                aws_region=payload.aws_region,
                template=template,
                plan=plan,
                selected_port=payload.selected_port,
                is_random_port=payload.is_random_port,
            )
            
            # TODO: Create nested resources (env vars, db config, etc.)
            
            return project

    @route.get("/{project_id}", response=ProjectRead, auth=django_auth)
    def get_project(self, request, project_id: UUID):
        """Get a specific project by ID"""
        project = get_object_or_404(Project, id=project_id, owner=request.user, deleted_at__isnull=True)
        return project

    @route.put("/{project_id}", response=ProjectRead, auth=django_auth)
    def update_project(self, request, project_id: UUID, payload: ProjectCreate):
        """
        Update an existing project.
        
        TODO: Implement update logic with proper validation
        """
        project = get_object_or_404(Project, id=project_id, owner=request.user, deleted_at__isnull=True)
        # TODO: Update project fields
        return project

    @route.delete("/{project_id}", auth=django_auth)
    def delete_project(self, request, project_id: UUID):
        """
        Soft delete a project.
        
        TODO: Implement soft delete and cleanup of related resources
        """
        project = get_object_or_404(Project, id=project_id, owner=request.user, deleted_at__isnull=True)
        # TODO: Set deleted_at timestamp
        return {"success": True}

    # Helper endpoints
    @route.get("/templates/", response=List[TemplateSchema])
    def list_templates(self, request):
        """List available project templates"""
        return Template.objects.all()

    @route.get("/plans/", response=List[PlanSchema])
    def list_plans(self, request):
        """List available pricing plans"""
        return Plan.objects.all()