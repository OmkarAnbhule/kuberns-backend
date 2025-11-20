from ninja_extra import ControllerBase, api_controller, route
from ninja.security import django_auth
from django.contrib.auth import get_user_model

from .schemas import UserSchema, UserCreateSchema, UserUpdateSchema, LoginSchema, LoginResponseSchema

User = get_user_model()


@api_controller("/accounts", tags=["Accounts"])
class AccountsController(ControllerBase):
    
    @route.get("/me", response=UserSchema, auth=django_auth)
    def get_current_user(self, request):
        """
        Get current authenticated user information.
        
        TODO: Add proper authentication and error handling
        """
        return request.user
    
    # TODO: Add more endpoints:
    # @route.post("/register")
    # def register(self, request, payload: UserCreateSchema):
    #     """Register new user"""
    #     pass
    
    # @route.post("/login")
    # def login(self, request, payload: LoginSchema):
    #     """User login"""
    #     pass
    
    # @route.post("/logout", auth=django_auth)
    # def logout(self, request):
    #     """User logout"""
    #     pass
    
    # @route.put("/profile", auth=django_auth)
    # def update_profile(self, request, payload: UserUpdateSchema):
    #     """Update user profile"""
    #     pass