from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

# Import controllers from each app
from apps.accounts.api import AccountsController
from apps.projects.api import ProjectsController
from apps.integrations.api import IntegrationsController
from apps.infra.api import InfraController

# Create NinjaExtraAPI instance
api = NinjaExtraAPI()

# Register JWT controller for token management
api.register_controllers(NinjaJWTDefaultController)

# Register app controllers
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
