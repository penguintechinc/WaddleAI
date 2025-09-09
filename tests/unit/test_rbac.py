"""
Unit tests for RBAC (Role-Based Access Control) system
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from shared.auth.rbac import RBACManager, Role, Permission, UserContext
from shared.auth.rbac import AuthenticationError, AuthorizationError


class TestRBACManager:
    """Test RBAC Manager functionality"""
    
    def test_init(self, mock_db):
        """Test RBAC manager initialization"""
        rbac = RBACManager(mock_db, "test-secret")
        assert rbac.db == mock_db
        assert rbac.secret_key == "test-secret"
    
    def test_hash_password(self, rbac_manager):
        """Test password hashing"""
        password = "testpassword123"
        hashed = rbac_manager.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 50  # Bcrypt hashes are long
    
    def test_verify_password(self, rbac_manager):
        """Test password verification"""
        password = "testpassword123"
        hashed = rbac_manager.hash_password(password)
        
        assert rbac_manager.verify_password(password, hashed) is True
        assert rbac_manager.verify_password("wrongpassword", hashed) is False
    
    def test_hash_api_key(self, rbac_manager):
        """Test API key hashing"""
        api_key = "wa-test-12345"
        hashed = rbac_manager.hash_api_key(api_key)
        
        assert hashed != api_key
        assert isinstance(hashed, str)
        assert len(hashed) > 50
    
    def test_generate_jwt_token(self, rbac_manager, sample_user_context):
        """Test JWT token generation"""
        token = rbac_manager.generate_jwt_token(sample_user_context)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        
        # Decode and verify token contents
        decoded = jwt.decode(token, rbac_manager.secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == sample_user_context.user_id
        assert decoded["username"] == sample_user_context.username
        assert decoded["role"] == sample_user_context.role.value
        assert decoded["organization_id"] == sample_user_context.organization_id
    
    def test_verify_jwt_token(self, rbac_manager, sample_user_context):
        """Test JWT token verification"""
        token = rbac_manager.generate_jwt_token(sample_user_context)
        verified_context = rbac_manager.verify_jwt_token(token)
        
        assert verified_context.user_id == sample_user_context.user_id
        assert verified_context.username == sample_user_context.username
        assert verified_context.role == sample_user_context.role
        assert verified_context.organization_id == sample_user_context.organization_id
    
    def test_verify_jwt_token_invalid(self, rbac_manager):
        """Test JWT token verification with invalid token"""
        with pytest.raises(AuthenticationError):
            rbac_manager.verify_jwt_token("invalid.token.here")
    
    def test_verify_jwt_token_expired(self, rbac_manager, sample_user_context):
        """Test JWT token verification with expired token"""
        # Create expired token
        expired_payload = {
            "user_id": sample_user_context.user_id,
            "username": sample_user_context.username,
            "role": sample_user_context.role.value,
            "organization_id": sample_user_context.organization_id,
            "permissions": sample_user_context.permissions,
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, rbac_manager.secret_key, algorithm="HS256")
        
        with pytest.raises(AuthenticationError):
            rbac_manager.verify_jwt_token(expired_token)
    
    @patch('shared.auth.rbac.bcrypt.checkpw')
    def test_authenticate_user(self, mock_checkpw, rbac_manager, mock_db):
        """Test user authentication"""
        mock_checkpw.return_value = True
        
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.password_hash = "hashed_password"
        mock_user.role = "user"
        mock_user.organization_id = 1
        mock_user.enabled = True
        
        mock_db.return_value = Mock()
        mock_db.return_value.select = Mock(return_value=[mock_user])
        mock_db.users = Mock()
        
        context = rbac_manager.authenticate_user("testuser", "testpassword")
        
        assert context is not None
        assert context.user_id == 1
        assert context.username == "testuser"
        assert context.role == Role.USER
        assert context.organization_id == 1
    
    def test_authenticate_user_invalid(self, rbac_manager, mock_db):
        """Test user authentication with invalid credentials"""
        mock_db.return_value = Mock()
        mock_db.return_value.select = Mock(return_value=[])  # No user found
        mock_db.users = Mock()
        
        context = rbac_manager.authenticate_user("invaliduser", "wrongpassword")
        assert context is None
    
    def test_check_permission_admin(self, rbac_manager, admin_user_context):
        """Test permission checking for admin user"""
        # Admin should have all permissions
        assert rbac_manager.check_permission(admin_user_context, Permission.ADMIN_MANAGE) is True
        assert rbac_manager.check_permission(admin_user_context, Permission.RESOURCE_MANAGE) is True
        assert rbac_manager.check_permission(admin_user_context, Permission.USER_READ) is True
    
    def test_check_permission_user(self, rbac_manager, sample_user_context):
        """Test permission checking for regular user"""
        # Regular user should only have user permissions
        assert rbac_manager.check_permission(sample_user_context, Permission.USER_READ) is True
        assert rbac_manager.check_permission(sample_user_context, Permission.ADMIN_MANAGE) is False
        assert rbac_manager.check_permission(sample_user_context, Permission.RESOURCE_MANAGE) is False
    
    def test_require_permission_success(self, rbac_manager, admin_user_context):
        """Test permission requirement (success case)"""
        # Should not raise exception
        rbac_manager.require_permission(admin_user_context, Permission.ADMIN_MANAGE)
    
    def test_require_permission_failure(self, rbac_manager, sample_user_context):
        """Test permission requirement (failure case)"""
        with pytest.raises(AuthorizationError):
            rbac_manager.require_permission(sample_user_context, Permission.ADMIN_MANAGE)


class TestRole:
    """Test Role enum"""
    
    def test_role_values(self):
        """Test role enum values"""
        assert Role.ADMIN.value == "admin"
        assert Role.RESOURCE_MANAGER.value == "resource_manager"
        assert Role.REPORTER.value == "reporter"
        assert Role.USER.value == "user"
    
    def test_role_hierarchy(self):
        """Test role hierarchy"""
        # Admin should have highest privileges
        admin_perms = set(Permission.get_permissions_for_role(Role.ADMIN))
        user_perms = set(Permission.get_permissions_for_role(Role.USER))
        
        # Admin permissions should include all user permissions
        assert user_perms.issubset(admin_perms)


class TestPermission:
    """Test Permission enum"""
    
    def test_permission_values(self):
        """Test permission enum values"""
        assert Permission.ADMIN_MANAGE.value == "admin:manage"
        assert Permission.RESOURCE_MANAGE.value == "resource:manage"
        assert Permission.USER_READ.value == "user:read"
    
    def test_get_permissions_for_role(self):
        """Test getting permissions for each role"""
        admin_perms = Permission.get_permissions_for_role(Role.ADMIN)
        assert Permission.ADMIN_MANAGE in admin_perms
        assert Permission.RESOURCE_MANAGE in admin_perms
        assert Permission.USER_READ in admin_perms
        
        user_perms = Permission.get_permissions_for_role(Role.USER)
        assert Permission.ADMIN_MANAGE not in user_perms
        assert Permission.USER_READ in user_perms
        
        resource_manager_perms = Permission.get_permissions_for_role(Role.RESOURCE_MANAGER)
        assert Permission.RESOURCE_MANAGE in resource_manager_perms
        assert Permission.ADMIN_MANAGE not in resource_manager_perms


class TestUserContext:
    """Test UserContext dataclass"""
    
    def test_user_context_creation(self):
        """Test UserContext creation"""
        context = UserContext(
            user_id=1,
            username="testuser",
            role=Role.USER,
            organization_id=1,
            api_key_id=1,
            permissions=["user:read"]
        )
        
        assert context.user_id == 1
        assert context.username == "testuser"
        assert context.role == Role.USER
        assert context.organization_id == 1
        assert context.api_key_id == 1
        assert context.permissions == ["user:read"]
    
    def test_user_context_defaults(self):
        """Test UserContext default values"""
        context = UserContext(
            user_id=1,
            username="testuser",
            role=Role.USER,
            organization_id=1
        )
        
        assert context.api_key_id is None
        assert context.permissions == []


class TestExceptions:
    """Test custom exceptions"""
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Invalid credentials")
    
    def test_authorization_error(self):
        """Test AuthorizationError"""
        with pytest.raises(AuthorizationError):
            raise AuthorizationError("Insufficient permissions")