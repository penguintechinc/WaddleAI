"""
Role-Based Access Control (RBAC) System
Handles authentication and authorization for WaddleAI
"""

from enum import Enum
from typing import List, Dict, Optional, Set
from passlib.hash import bcrypt
import jwt
from datetime import datetime, timedelta
import functools
from dataclasses import dataclass


class Role(Enum):
    """User roles with hierarchical permissions"""
    ADMIN = "admin"
    RESOURCE_MANAGER = "resource_manager"
    REPORTER = "reporter"
    USER = "user"


class Permission(Enum):
    """System permissions"""
    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_HEALTH = "system:health"
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Organization management
    ORG_CREATE = "org:create"
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    
    # API key management
    APIKEY_CREATE = "apikey:create"
    APIKEY_READ = "apikey:read"
    APIKEY_UPDATE = "apikey:update"
    APIKEY_DELETE = "apikey:delete"
    
    # Quota management
    QUOTA_READ = "quota:read"
    QUOTA_UPDATE = "quota:update"
    QUOTA_RESET = "quota:reset"
    
    # Analytics and reporting
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_SYSTEM = "analytics:system"
    ANALYTICS_SECURITY = "analytics:security"
    
    # LLM management
    LLM_CONFIG = "llm:config"
    LLM_MODELS = "llm:models"
    
    # Proxy usage
    PROXY_USE = "proxy:use"
    PROXY_ROUTE = "proxy:route"


@dataclass
class UserContext:
    """User context for authorization"""
    user_id: int
    username: str
    role: Role
    organization_id: int
    managed_orgs: List[int]
    permissions: Set[Permission]
    api_key_id: Optional[int] = None


# Role-based permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        # Full system access
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_MONITOR,
        Permission.SYSTEM_HEALTH,
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.ORG_CREATE,
        Permission.ORG_READ,
        Permission.ORG_UPDATE,
        Permission.ORG_DELETE,
        Permission.APIKEY_CREATE,
        Permission.APIKEY_READ,
        Permission.APIKEY_UPDATE,
        Permission.APIKEY_DELETE,
        Permission.QUOTA_READ,
        Permission.QUOTA_UPDATE,
        Permission.QUOTA_RESET,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_SYSTEM,
        Permission.ANALYTICS_SECURITY,
        Permission.LLM_CONFIG,
        Permission.LLM_MODELS,
        Permission.PROXY_USE,
        Permission.PROXY_ROUTE,
    },
    Role.RESOURCE_MANAGER: {
        Permission.SYSTEM_HEALTH,
        Permission.USER_READ,
        Permission.USER_UPDATE,  # For assigned orgs
        Permission.ORG_READ,
        Permission.ORG_UPDATE,  # For assigned orgs
        Permission.APIKEY_CREATE,  # For assigned orgs
        Permission.APIKEY_READ,
        Permission.APIKEY_UPDATE,
        Permission.QUOTA_READ,
        Permission.QUOTA_UPDATE,  # For assigned orgs
        Permission.QUOTA_RESET,   # For assigned orgs
        Permission.ANALYTICS_READ,
        Permission.PROXY_USE,
    },
    Role.REPORTER: {
        Permission.SYSTEM_HEALTH,
        Permission.USER_READ,     # For assigned orgs
        Permission.ORG_READ,      # For assigned orgs
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_SECURITY,
        Permission.PROXY_USE,
    },
    Role.USER: {
        Permission.SYSTEM_HEALTH,
        Permission.APIKEY_CREATE,  # Own keys only
        Permission.APIKEY_READ,    # Own keys only
        Permission.APIKEY_UPDATE,  # Own keys only
        Permission.QUOTA_READ,     # Own quota only
        Permission.ANALYTICS_READ, # Own usage only
        Permission.PROXY_USE,
    }
}


class AuthenticationError(Exception):
    """Authentication failed"""
    pass


class AuthorizationError(Exception):
    """Authorization failed"""
    pass


class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self, db, jwt_secret: str):
        self.db = db
        self.jwt_secret = jwt_secret
    
    def authenticate_user(self, username: str, password: str) -> UserContext:
        """Authenticate user with username/password"""
        user = self.db(
            (self.db.users.username == username) &
            (self.db.users.enabled == True)
        ).select().first()
        
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        if not bcrypt.verify(password, user.password_hash):
            raise AuthenticationError("Invalid username or password")
        
        return self._build_user_context(user)
    
    def authenticate_api_key(self, api_key: str) -> UserContext:
        """Authenticate user with API key"""
        # Extract key ID from API key (format: wa-{key_id}-{secret})
        try:
            parts = api_key.split('-')
            if len(parts) < 3 or parts[0] != 'wa':
                raise AuthenticationError("Invalid API key format")
        except:
            raise AuthenticationError("Invalid API key format")
        
        # Find API key by checking hash
        api_keys = self.db(
            (self.db.api_keys.enabled == True)
        ).select()
        
        for key_record in api_keys:
            if bcrypt.verify(api_key, key_record.key_hash):
                # Update last used
                key_record.update_record(last_used=datetime.utcnow())
                
                # Get user
                user = self.db(self.db.users.id == key_record.user_id).select().first()
                if not user or not user.enabled:
                    raise AuthenticationError("API key user is disabled")
                
                context = self._build_user_context(user)
                context.api_key_id = key_record.id
                return context
        
        raise AuthenticationError("Invalid API key")
    
    def _build_user_context(self, user) -> UserContext:
        """Build user context from database record"""
        role = Role(user.role)
        permissions = ROLE_PERMISSIONS.get(role, set())
        
        managed_orgs = []
        if user.managed_orgs:
            managed_orgs = [int(org_id) for org_id in user.managed_orgs]
        
        return UserContext(
            user_id=user.id,
            username=user.username,
            role=role,
            organization_id=user.organization_id,
            managed_orgs=managed_orgs,
            permissions=permissions
        )
    
    def generate_jwt_token(self, user_context: UserContext, expires_hours: int = 24) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user_context.user_id,
            'username': user_context.username,
            'role': user_context.role.value,
            'organization_id': user_context.organization_id,
            'managed_orgs': user_context.managed_orgs,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> UserContext:
        """Verify JWT token and return user context"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            role = Role(payload['role'])
            permissions = ROLE_PERMISSIONS.get(role, set())
            
            return UserContext(
                user_id=payload['user_id'],
                username=payload['username'],
                role=role,
                organization_id=payload['organization_id'],
                managed_orgs=payload.get('managed_orgs', []),
                permissions=permissions
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def check_permission(
        self, 
        user_context: UserContext, 
        permission: Permission,
        resource_org_id: Optional[int] = None,
        resource_user_id: Optional[int] = None
    ) -> bool:
        """Check if user has permission for specific resource"""
        
        # Check base permission
        if permission not in user_context.permissions:
            return False
        
        # Admin has access to everything
        if user_context.role == Role.ADMIN:
            return True
        
        # Resource-specific checks
        if resource_org_id is not None:
            # Resource managers can only access their assigned orgs
            if user_context.role == Role.RESOURCE_MANAGER:
                if resource_org_id not in user_context.managed_orgs:
                    return False
            
            # Reporters can only access their assigned orgs
            elif user_context.role == Role.REPORTER:
                if resource_org_id not in user_context.managed_orgs:
                    return False
            
            # Users can only access their own organization
            elif user_context.role == Role.USER:
                if resource_org_id != user_context.organization_id:
                    return False
        
        # User-specific checks
        if resource_user_id is not None:
            # Users can only access their own data
            if user_context.role == Role.USER:
                if resource_user_id != user_context.user_id:
                    return False
        
        return True
    
    def require_permission(self, permission: Permission, resource_org_id: Optional[int] = None):
        """Decorator to require specific permission"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user context from request/kwargs
                user_context = kwargs.get('user_context')
                if not user_context:
                    raise AuthorizationError("No user context provided")
                
                if not self.check_permission(user_context, permission, resource_org_id):
                    raise AuthorizationError(f"Permission denied: {permission.value}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def create_api_key(
        self, 
        user_context: UserContext,
        name: str,
        permissions: Dict[str, bool] = None,
        expires_days: Optional[int] = None
    ) -> tuple[str, str]:
        """Create new API key for user"""
        import secrets
        
        # Generate API key
        key_id = secrets.token_hex(8)
        secret = secrets.token_urlsafe(32)
        api_key = f"wa-{key_id}-{secret}"
        
        # Hash the API key
        key_hash = bcrypt.hash(api_key)
        
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Determine access level based on user role
        access_level = "proxy_api"
        if user_context.role in [Role.ADMIN, Role.RESOURCE_MANAGER]:
            access_level = "management_api"
        if user_context.role == Role.ADMIN:
            access_level = "admin_api"
        
        # Insert into database
        key_record_id = self.db.api_keys.insert(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_context.user_id,
            organization_id=user_context.organization_id,
            name=name,
            permissions=permissions or {},
            api_access_level=access_level,
            expires_at=expires_at
        )
        
        return api_key, key_record_id


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.verify(password, hashed)