"""
JWT Authentication routes for frontend user management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from jwt_auth import (
    JWTAuthService, UserCreate, UserLogin, UserResponse, TokenResponse
)

# Security scheme for JWT tokens
jwt_security = HTTPBearer(auto_error=False)

# Router for auth endpoints
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Global service - will be initialized in main server
jwt_auth_service: Optional[JWTAuthService] = None


def init_jwt_auth_service(db):
    """Initialize JWT auth service with database."""
    global jwt_auth_service
    jwt_auth_service = JWTAuthService(db.users)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(jwt_security)
) -> UserResponse:
    """
    Get current authenticated user from JWT token.
    
    This dependency can be used in routes that require user authentication.
    """
    if not jwt_auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await jwt_auth_service.get_current_user_from_token(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Authentication endpoints
@auth_router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserCreate):
    """
    Register a new user account.
    
    Creates a new user and returns an access token for immediate login.
    """
    if not jwt_auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    try:
        # Create user
        user = await jwt_auth_service.create_user(user_data)
        
        # Generate access token
        token_data = jwt_auth_service.create_access_token({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
        
        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@auth_router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """
    Authenticate user and return access token.
    
    Accepts username or email with password for authentication.
    """
    if not jwt_auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    try:
        # Authenticate user
        user = await jwt_auth_service.authenticate_user(
            login_data.username, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Generate access token
        token_data = jwt_auth_service.create_access_token({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
        
        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user information.
    
    Returns the profile information for the authenticated user.
    """
    return current_user


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: UserResponse = Depends(get_current_user)):
    """
    Refresh access token.
    
    Generates a new access token for the current user.
    """
    if not jwt_auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not available"
        )
    
    try:
        # Generate new access token
        token_data = jwt_auth_service.create_access_token({
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        })
        
        return TokenResponse(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=current_user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@auth_router.post("/logout")
async def logout_user(current_user: UserResponse = Depends(get_current_user)):
    """
    Logout user.
    
    Note: With JWT tokens, logout is mainly handled client-side by discarding the token.
    This endpoint is provided for consistency and potential future token blacklisting.
    """
    return {
        "message": "Logged out successfully",
        "user": current_user.username
    }


# Public endpoint for testing auth status
@auth_router.get("/status")
async def auth_status():
    """
    Get authentication system status.
    
    Public endpoint for checking if JWT auth is working.
    """
    return {
        "auth_system": "jwt",
        "service_available": jwt_auth_service is not None,
        "endpoints": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login", 
            "me": "GET /api/auth/me (requires token)",
            "refresh": "POST /api/auth/refresh (requires token)",
            "logout": "POST /api/auth/logout (requires token)"
        },
        "token_type": "Bearer",
        "token_expiry": "24 hours"
    }