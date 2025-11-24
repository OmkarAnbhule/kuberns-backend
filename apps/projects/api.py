from ninja_extra import ControllerBase, api_controller, route
from django.shortcuts import aget_object_or_404
from typing import List
from uuid import UUID
from ninja_jwt.authentication import AsyncJWTAuth

from apps.core.exceptions import handle_api_exception
from .models import Project, Template, Plan, DatabaseConfig, EnvVar
from .schemas import (
    ProjectCreate,
    ProjectRead,
    TemplateSchema,
    PlanSchema,
    CreateProjectResponse,
)


@api_controller("/projects", tags=["Projects"])
class ProjectsController(ControllerBase):

    @route.get("/getAll", response=List[ProjectRead], auth=AsyncJWTAuth())
    @handle_api_exception
    async def list_projects(self, request):
        """
        List all projects for the authenticated user.

        TODO: Add pagination, filtering, and sorting
        """
        projects = [
            p
            async for p in Project.objects.prefetch_related("env_vars")
            .select_related("template", "plan")
            .filter(owner=request.user, deleted_at__isnull=True)
        ]
        return projects

    @route.post("/create", response=CreateProjectResponse, auth=AsyncJWTAuth())
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

        template = await Template.objects.filter(id=payload.template_id).afirst()
        if not template:
            raise ValueError("Invalid template ID")
        plan = await Plan.objects.filter(id=payload.plan_id).afirst()
        if not plan:
            raise ValueError("Invalid plan ID")

        # Create project
        project = await Project.objects.prefetch_related("env_vars").acreate(
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
                    is_secret=env_var.is_secret,
                )
                for env_var in payload.env_vars
            ]
            await EnvVar.objects.abulk_create(env_vars_to_create)

        # Create database config if provided
        if payload.database_config and payload.database_config.connection_url:
            await DatabaseConfig.objects.acreate(
                project=project,
                connection_url_encrypted=payload.database_config.connection_url,
            )

        # Refresh to get related objects
        await project.arefresh_from_db()

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
        project = await Project.objects.select_related("template","plan","databaseconfig").prefetch_related("env_vars").filter(id=project_id, owner=request.user, deleted_at__isnull=True).afirst()
        
        if not project:
            raise ValueError("Project not found")
        
        if payload.name:
            project.name = payload.name
        if payload.aws_region:
            project.aws_region = payload.aws_region
        if payload.template_id:
            project.template = await Template.objects.filter(
                id=payload.template_id
            ).afirst()
        if payload.plan_id:
            project.plan = await Plan.objects.filter(id=payload.plan_id).afirst()
        if payload.organization:
            project.organization = payload.organization
        if payload.repository_name:
            project.repository_name = payload.repository_name
        if payload.branch_name:
            project.branch_name = payload.branch_name
        if payload.selected_port:
            project.selected_port = payload.selected_port
        if payload.is_random_port:
            project.is_random_port = payload.is_random_port
        if payload.env_vars:
            keys = [env.key for env in payload.env_vars]

            # Fetch existing env vars for these keys
            existing_env_vars = {
                obj.key: obj
                async for obj in EnvVar.objects.filter(project=project, key__in=keys).all()
            }

            to_update = []
            to_create = []

            for env in payload.env_vars:
                if env.key in existing_env_vars:
                    # Update existing
                    obj = existing_env_vars[env.key]
                    obj.value_encrypted = env.value
                    obj.is_secret = env.is_secret
                    to_update.append(obj)
                else:
                    # Create new
                    to_create.append(
                        EnvVar(
                            project=project,
                            key=env.key,
                            value_encrypted=env.value,
                            is_secret=env.is_secret,
                        )
                    )

            # Bulk create new env vars
            if to_create:
                await EnvVar.objects.abulk_create(to_create)

            # Bulk update existing env vars
            if to_update:
                await EnvVar.objects.abulk_update(to_update, fields=["value_encrypted", "is_secret"])

        if payload.database_config and payload.database_config.connection_url:
            project.databaseconfig.connection_url_encrypted = (
                payload.database_config.connection_url
            )
        await project.asave()
        return project


    @route.delete("/{project_id}/", auth=AsyncJWTAuth())
    @handle_api_exception
    async def delete_project(self, request, project_id: UUID):
        """
        Soft delete a project.

        TODO: Implement soft delete and cleanup of related resources
        """
        project = await Project.objects.select_related("template","plan").prefetch_related("env_vars").filter(id=project_id, owner=request.user, deleted_at__isnull=True).afirst()
        
        if not project:
            raise ValueError("Project not found")
        
        await project.adelete()
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
