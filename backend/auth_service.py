"""
Authentication service for API key management.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from loguru import logger

from scraper_models import ApiKeyCreate, ApiKeyResponse, ApiKeyInfo


class AuthService:
    """
    Service for managing API key authentication.
    """
    
    def __init__(self, db_collection):
        """
        Initialize the authentication service.
        
        Args:
            db_collection: MongoDB collection for storing API keys
        """
        self.db = db_collection
        
    def _generate_api_key(self) -> str:
        """Generate a secure random API key."""
        return f"scraper_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(32))}"
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(self, request: ApiKeyCreate) -> ApiKeyResponse:
        """
        Create a new API key.
        
        Args:
            request: API key creation request
            
        Returns:
            ApiKeyResponse with the new key
        """
        # Generate key and ID
        key_id = str(uuid.uuid4())
        api_key = self._generate_api_key()
        key_hash = self._hash_api_key(api_key)
        
        # Calculate expiration
        expires_at = None
        if request.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
        
        # Create key document
        key_doc = {
            "key_id": key_id,
            "name": request.name,
            "key_hash": key_hash,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True
        }
        
        # Store in database
        await self.db.insert_one(key_doc)
        
        logger.info(f"Created new API key '{request.name}' with ID {key_id}")
        
        return ApiKeyResponse(
            key_id=key_id,
            name=request.name,
            api_key=api_key,  # Only returned once during creation
            expires_at=expires_at,
            created_at=key_doc["created_at"]
        )
    
    async def validate_api_key(self, api_key: str) -> Optional[str]:
        """
        Validate an API key and return the key ID if valid.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Key ID if valid, None otherwise
        """
        if not api_key or not api_key.startswith("scraper_"):
            return None
        
        try:
            key_hash = self._hash_api_key(api_key)
            
            # Find key in database
            key_doc = await self.db.find_one({
                "key_hash": key_hash,
                "is_active": True
            })
            
            if not key_doc:
                return None
            
            # Check expiration
            if key_doc.get("expires_at") and key_doc["expires_at"] < datetime.utcnow():
                logger.warning(f"API key {key_doc['key_id']} has expired")
                return None
            
            # Update last used timestamp
            await self.db.update_one(
                {"key_id": key_doc["key_id"]},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            
            return key_doc["key_id"]
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    async def list_api_keys(self) -> List[ApiKeyInfo]:
        """
        List all API keys (without the actual key values).
        
        Returns:
            List of ApiKeyInfo objects
        """
        cursor = self.db.find().sort("created_at", -1)
        keys = []
        
        async for doc in cursor:
            # Check if expired
            is_active = doc.get("is_active", True)
            if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
                is_active = False
            
            keys.append(ApiKeyInfo(
                key_id=doc["key_id"],
                name=doc["name"],
                expires_at=doc.get("expires_at"),
                created_at=doc["created_at"],
                last_used=doc.get("last_used"),
                is_active=is_active
            ))
        
        return keys
    
    async def get_api_key_info(self, key_id: str) -> Optional[ApiKeyInfo]:
        """
        Get information about a specific API key.
        
        Args:
            key_id: Key identifier
            
        Returns:
            ApiKeyInfo if found, None otherwise
        """
        doc = await self.db.find_one({"key_id": key_id})
        if not doc:
            return None
        
        # Check if expired
        is_active = doc.get("is_active", True)
        if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
            is_active = False
        
        return ApiKeyInfo(
            key_id=doc["key_id"],
            name=doc["name"],
            expires_at=doc.get("expires_at"),
            created_at=doc["created_at"],
            last_used=doc.get("last_used"),
            is_active=is_active
        )
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke (deactivate) an API key.
        
        Args:
            key_id: Key identifier
            
        Returns:
            True if revoked successfully, False if not found
        """
        result = await self.db.update_one(
            {"key_id": key_id},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Revoked API key {key_id}")
            return True
        else:
            logger.warning(f"API key {key_id} not found for revocation")
            return False
    
    async def delete_api_key(self, key_id: str) -> bool:
        """
        Permanently delete an API key.
        
        Args:
            key_id: Key identifier
            
        Returns:
            True if deleted successfully, False if not found
        """
        result = await self.db.delete_one({"key_id": key_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted API key {key_id}")
            return True
        else:
            logger.warning(f"API key {key_id} not found for deletion")
            return False