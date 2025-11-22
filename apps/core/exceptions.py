"""
Centralized exception handling for all API endpoints
"""

from typing import Any, Dict, Optional, Callable
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError, DatabaseError
import logging

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base exception for API errors"""
    
    def __init__(self, message: str, status_code: int = 400, details: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BadRequestException(APIException):
    """400 Bad Request"""
    def __init__(self, message: str = "Bad request", details: Optional[Dict] = None):
        super().__init__(message, 400, details)


class UnauthorizedException(APIException):
    """401 Unauthorized"""
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict] = None):
        super().__init__(message, 401, details)


class ForbiddenException(APIException):
    """403 Forbidden"""
    def __init__(self, message: str = "Forbidden", details: Optional[Dict] = None):
        super().__init__(message, 403, details)


class NotFoundException(APIException):
    """404 Not Found"""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict] = None):
        super().__init__(message, 404, details)


class ConflictException(APIException):
    """409 Conflict"""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict] = None):
        super().__init__(message, 409, details)


class InternalServerException(APIException):
    """500 Internal Server Error"""
    def __init__(self, message: str = "Internal server error", details: Optional[Dict] = None):
        super().__init__(message, 500, details)


def handle_api_exception(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in API endpoints
    
    Usage:
        @route.get("/endpoint")
        @handle_api_exception
        async def my_endpoint(self, request):
            # Your code here
    """
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        
        except APIException as e:
            logger.warning(f"API Exception: {e.message}", extra={
                "status_code": e.status_code,
                "details": e.details
            })
            return JsonResponse({
                "success": False,
                "error": e.message,
                "details": e.details
            }, status=e.status_code)
        
        except ObjectDoesNotExist as e:
            logger.warning(f"Object not found: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Resource not found",
                "details": {"message": str(e)}
            }, status=404)
        
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Permission denied",
                "details": {"message": str(e)}
            }, status=403)
        
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Validation error",
                "details": {"message": str(e)}
            }, status=400)
        
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Database integrity error",
                "details": {"message": "A database constraint was violated"}
            }, status=409)
        
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Database error",
                "details": {"message": "A database error occurred"}
            }, status=500)
        
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return JsonResponse({
                "success": False,
                "error": "Internal server error",
                "details": {"message": "An unexpected error occurred"}
            }, status=500)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except APIException as e:
            logger.warning(f"API Exception: {e.message}", extra={
                "status_code": e.status_code,
                "details": e.details
            })
            return JsonResponse({
                "success": False,
                "error": e.message,
                "details": e.details
            }, status=e.status_code)
        
        except ObjectDoesNotExist as e:
            logger.warning(f"Object not found: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Resource not found",
                "details": {"message": str(e)}
            }, status=404)
        
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Permission denied",
                "details": {"message": str(e)}
            }, status=403)
        
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Validation error",
                "details": {"message": str(e)}
            }, status=400)
        
        except IntegrityError as e:
            logger.error(f"Database integrity error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Database integrity error",
                "details": {"message": "A database constraint was violated"}
            }, status=409)
        
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}")
            return JsonResponse({
                "success": False,
                "error": "Database error",
                "details": {"message": "A database error occurred"}
            }, status=500)
        
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return JsonResponse({
                "success": False,
                "error": "Internal server error",
                "details": {"message": "An unexpected error occurred"}
            }, status=500)
    
    # Return appropriate wrapper based on whether function is async
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def create_error_response(
    message: str,
    status_code: int = 400,
    details: Optional[Dict] = None
) -> JsonResponse:
    """
    Helper function to create standardized error responses
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        JsonResponse with error information
    """
    return JsonResponse({
        "success": False,
        "error": message,
        "details": details or {}
    }, status=status_code)


def create_success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> JsonResponse:
    """
    Helper function to create standardized success responses
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
    
    Returns:
        JsonResponse with success information
    """
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return JsonResponse(response, status=status_code)
