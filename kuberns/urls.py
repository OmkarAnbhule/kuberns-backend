from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI

# Import controllers from each app
from apps.accounts.api import AccountsController
from apps.projects.api import ProjectsController
from apps.integrations.api import IntegrationsController
from apps.infra.api import InfraController

# Create NinjaExtraAPI instance
api = NinjaExtraAPI()

# Register controllers
api.register_controllers(
    AccountsController,
    ProjectsController,
    IntegrationsController,
    InfraController,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
