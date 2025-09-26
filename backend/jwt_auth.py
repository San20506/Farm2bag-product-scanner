"""
JWT Authentication service for frontend user management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os
from fastapi import HTTPException, status


# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    """Model for user creation."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Model for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class JWTAuthService:
    """
    JWT Authentication service for UI users.
    Works alongside API key authentication for programmatic access.
    """
    
    def __init__(self, db_collection):
        """
        Initialize JWT auth service.
        
        Args:
            db_collection: MongoDB collection for storing users
        """
        self.db = db_collection
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a JWT access token.
        
        Args:
            user_data: User information to encode in token
            
        Returns:
            Token data with expiration info
        """
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        
        to_encode = {
            "sub": user_data["username"],  # Subject
            "user_id": user_data["id"],
            "email": user_data["email"],
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "type": "access_token"
        }
        
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        return {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRE_HOURS * 3600,  # seconds
            "expires_at": expire
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check if token is expired
            if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user account.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user information
            
        Raises:
            HTTPException if username/email already exists
        """
        # Check if username already exists
        existing_user = await self.db.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await self.db.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user document
        import uuid
        user_doc = {
            "id": str(uuid.uuid4()),
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": self.hash_password(user_data.password),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Store in database
        await self.db.insert_one(user_doc)
        
        # Return user info (without password)
        return UserResponse(
            id=user_doc["id"],
            username=user_doc["username"],
            email=user_doc["email"],
            full_name=user_doc["full_name"],
            is_active=user_doc["is_active"],
            created_at=user_doc["created_at"]
        )
    
    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """
        Authenticate a user login.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User information if authenticated, None otherwise
        """
        # Find user by username or email
        user_doc = await self.db.find_one({
            "$or": [
                {"username": username},
                {"email": username}
            ]
        })
        
        if not user_doc:
            return None
        
        # Verify password
        if not self.verify_password(password, user_doc["password_hash"]):
            return None
        
        # Update last login
        await self.db.update_one(
            {"id": user_doc["id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Return user info
        return UserResponse(
            id=user_doc["id"],
            username=user_doc["username"],
            email=user_doc["email"],
            full_name=user_doc.get("full_name"),
            is_active=user_doc["is_active"],
            created_at=user_doc["created_at"]
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        user_doc = await self.db.find_one({"id": user_id})
        
        if not user_doc:
            return None
        
        return UserResponse(
            id=user_doc["id"],
            username=user_doc["username"],
            email=user_doc["email"],
            full_name=user_doc.get("full_name"),
            is_active=user_doc["is_active"],
            created_at=user_doc["created_at"]
        )
    
    async def get_current_user_from_token(self, token: str) -> Optional[UserResponse]:
        """
        Get current user from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            Current user information or None if invalid
        """
        payload = self.verify_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        return await self.get_user_by_id(user_id)