from ninja_extra import ControllerBase, api_controller, route
from django.shortcuts import aget_object_or_404
from typing import List
from uuid import UUID
from ninja_jwt.authentication import AsyncJWTAuth

from apps.core.exceptions import handle_api_exception
from .models import Project, Template, Plan, DatabaseConfig, EnvVar
from .schemas import ProjectCreate, ProjectRead, TemplateSchema, PlanSchema


@api_controller("/projects", tags=["Projects"])
class ProjectsController(ControllerBase):

    @route.get("/", response=List[ProjectRead], auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_projects(self, request):
        """
        List all projects for the authenticated user.

        TODO: Add pagination, filtering, and sorting
        """
        projects = [
            p
            async for p in Project.objects.filter(
                owner=request.user, deleted_at__isnull=True
            )
        ]
        return projects

    @route.post("/", response=ProjectRead, auth=AsyncJWTAuth())
    @handle_api_exception
    async def create_project(self, request, payload: ProjectCreate):
        """
        Create a new project with nested resources.

        Creates project with:
        - Template and plan validation
        - Environment variables
        - Database configuration (if provided)
        - GitHub repo association (if provided)
        """

        template = Template.objects.get(id=payload.template_id)
        plan = Plan.objects.get(id=payload.plan_id)

        # Create project
        project = Project.objects.create(
            owner=request.user,
            name=payload.name,
            aws_region=payload.aws_region,
            template=template,
            plan=plan,
            organization=payload.organization,
            repository_name=payload.repository_name,
            branch_name=payload.branch_name,
            selected_port=payload.selected_port,
            is_random_port=payload.is_random_port,
        )

        # Create environment variables
        if payload.env_vars:
            env_vars_to_create = [
                EnvVar(
                    project=project,
                    key=env_var.key,
                    value_encrypted=env_var.value,
                )
                for env_var in payload.env_vars
            ]
            EnvVar.objects.bulk_create(env_vars_to_create)

        # Create database config if provided
        if payload.database_config and payload.database_config.connection_url:
            DatabaseConfig.objects.create(
                project=project,
                connection_url_encrypted=payload.database_config.connection_url,
            )

        # Refresh to get related objects
        project.refresh_from_db()

        return project

    @route.get("/{project_id}/", response=ProjectRead, auth=AsyncJWTAuth())
    @handle_api_exception
    async def get_project(self, request, project_id: UUID):
        """Get a specific project by ID"""
        project = await aget_object_or_404(
            Project, id=project_id, owner=request.user, deleted_at__isnull=True
        )
        return project

    @route.put("/{project_id}/", response=ProjectRead, auth=AsyncJWTAuth())
    @handle_api_exception
    async def update_project(self, request, project_id: UUID, payload: ProjectCreate):
        """
        Update an existing project.

        TODO: Implement update logic with proper validation
        """
        project = await aget_object_or_404(
            Project, id=project_id, owner=request.user, deleted_at__isnull=True
        )
        # TODO: Update project fields
        return project

    @route.delete("/{project_id}/", auth=AsyncJWTAuth())
    @handle_api_exception
    async def delete_project(self, request, project_id: UUID):
        """
        Soft delete a project.

        TODO: Implement soft delete and cleanup of related resources
        """
        project = await aget_object_or_404(
            Project, id=project_id, owner=request.user, deleted_at__isnull=True
        )
        # TODO: Set deleted_at timestamp
        return {"success": True}

    # Helper endpoints
    @route.get("/templates", response=List[TemplateSchema], auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_templates(self, request):
        """List available project templates"""
        return [t async for t in Template.objects.all()]

    @route.get("/plans", response=List[PlanSchema], auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_plans(self, request):
        """List available pricing plans"""
        return [p async for p in Plan.objects.all()]
