"""
WaddleAI Management Server
Web-based administration portal with RBAC configuration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from py4web import action, request, response, redirect, URL, Field, abort
from py4web.utils.form import Form, FormStyleBulma
from py4web.utils.grid import Grid, GridClassStyleBulma
from py4web.utils.auth import Auth
from py4web.core import Session, Fixture
import uvicorn
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import structlog
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from shared.database.models import get_db, init_default_data
from shared.auth.rbac import RBACManager, AuthenticationError, AuthorizationError, Permission, Role
from shared.utils.llm_connectors import create_llm_connection_manager
from shared.utils.request_router import create_request_router
from shared.utils.mcp_interface import create_mcp_server
from shared.utils.metrics import get_management_metrics
from shared.utils.health_checks import WaddleAIHealthMonitor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Initialize metrics
management_metrics = get_management_metrics()


class ManagementServer:
    """WaddleAI Management Server"""
    
    def __init__(self):
        self.db = None
        self.rbac = None
        self.llm_manager = None
        self.request_router = None
        self.mcp_server = None
        self.mcp_websocket_server = None
        self.health_monitor = None
        self.metrics = management_metrics
        
        # Configuration
        self.config = {
            'jwt_secret': os.getenv('JWT_SECRET', 'your-secret-key-change-in-production'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
            'admin_username': os.getenv('ADMIN_USERNAME', 'admin'),
            'admin_password': os.getenv('ADMIN_PASSWORD', 'admin123'),
            'mcp_host': os.getenv('MCP_HOST', 'localhost'),
            'mcp_port': int(os.getenv('MCP_PORT', '8765')),
            'mcp_auto_start': os.getenv('MCP_AUTO_START', 'false').lower() == 'true'
        }
    
    async def startup(self):
        """Initialize server components"""
        logger.info("Starting WaddleAI Management Server")
        
        # Initialize database
        self.db = get_db()
        init_default_data(self.db)
        
        # Initialize components
        self.rbac = RBACManager(self.db, self.config['jwt_secret'])
        self.llm_manager = create_llm_connection_manager(self.db)
        self.request_router = create_request_router(self.llm_manager, self.db)
        self.mcp_server = create_mcp_server(self.rbac, self.request_router, self.db)
        
        # Initialize health monitoring
        self.health_monitor = WaddleAIHealthMonitor('management')
        self.health_monitor.add_database_check('database', self.db)
        self.health_monitor.add_redis_check('redis', self.config['redis_url'])
        self.health_monitor.add_system_resources_check()
        self.health_monitor.add_llm_providers_check('llm_providers', self.llm_manager)
        
        # Ensure admin user exists
        await self._ensure_admin_user()
        
        # Auto-start MCP server if configured
        if self.config['mcp_auto_start']:
            try:
                await self.start_mcp_server()
            except Exception as e:
                logger.error(f"Failed to auto-start MCP server: {e}")
        
        logger.info("Management server initialized successfully")
    
    async def shutdown(self):
        """Cleanup server components"""
        # Stop MCP server if running
        await self.stop_mcp_server()
        
        if self.llm_manager:
            await self.llm_manager.close_all()
        logger.info("Management server shutdown complete")
    
    async def start_mcp_server(self):
        """Start MCP WebSocket server"""
        if self.mcp_websocket_server:
            logger.warning("MCP server already running")
            return
        
        try:
            self.mcp_websocket_server = await self.mcp_server.start_server(
                host=self.config['mcp_host'],
                port=self.config['mcp_port']
            )
            logger.info(f"MCP server started on ws://{self.config['mcp_host']}:{self.config['mcp_port']}")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop_mcp_server(self):
        """Stop MCP WebSocket server"""
        if self.mcp_websocket_server:
            try:
                self.mcp_websocket_server.close()
                await self.mcp_websocket_server.wait_closed()
                self.mcp_websocket_server = None
                logger.info("MCP server stopped")
            except Exception as e:
                logger.error(f"Failed to stop MCP server: {e}")
    
    async def _ensure_admin_user(self):
        """Ensure admin user exists"""
        try:
            # Check if admin user exists
            admin_user = self.db(self.db.users.username == self.config['admin_username']).select().first()
            
            if not admin_user:
                # Create default organization
                org = self.db.organizations.insert(
                    name="Default Organization",
                    description="Default organization for admin user",
                    token_quota_daily=100000,
                    token_quota_monthly=3000000,
                    enabled=True
                )
                
                # Create admin user
                user_id = self.db.users.insert(
                    username=self.config['admin_username'],
                    email="admin@waddleai.com",
                    password_hash=self.rbac.hash_password(self.config['admin_password']),
                    role=Role.ADMIN,
                    organization_id=org,
                    enabled=True
                )
                
                # Create admin API key
                api_key = f"wa-admin-{user_id}-{datetime.utcnow().strftime('%Y%m%d')}"
                self.db.api_keys.insert(
                    key_hash=self.rbac.hash_api_key(api_key),
                    name="Admin API Key",
                    user_id=user_id,
                    organization_id=org,
                    permissions=["admin:*"],
                    enabled=True,
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
                
                logger.info(f"Created admin user with API key: {api_key}")
                print(f"🔑 Admin API Key: {api_key}")
                
        except Exception as e:
            logger.error(f"Failed to ensure admin user: {e}")


# Global server instance
mgmt_server = ManagementServer()


# FastAPI lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    await mgmt_server.startup()
    yield
    await mgmt_server.shutdown()


# Create FastAPI app
app = FastAPI(
    title="WaddleAI Management Server",
    description="Web-based administration portal with RBAC configuration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
templates = Jinja2Templates(directory="templates")


# Authentication dependency
async def get_current_user(request: FastAPIRequest):
    """Extract and validate user from request"""
    # Check for Authorization header (API key or JWT)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        try:
            # Try JWT first
            user_context = mgmt_server.rbac.verify_jwt_token(token)
            if user_context:
                return user_context
        except:
            pass
        
        try:
            # Try API key
            user_context = mgmt_server.rbac.verify_api_key(token)
            if user_context:
                return user_context
        except:
            pass
    
    # Check for session cookie
    session_token = request.cookies.get("session")
    if session_token:
        try:
            user_context = mgmt_server.rbac.verify_jwt_token(session_token)
            if user_context:
                return user_context
        except:
            pass
    
    raise HTTPException(status_code=401, detail="Authentication required")


# Health and metrics endpoints
@app.get("/healthz")
async def health_check():
    """Kubernetes-style health check"""
    try:
        health_results = await mgmt_server.health_monitor.check_all()
        if health_results['status'] == 'healthy':
            return "healthy"
        else:
            raise HTTPException(status_code=503, detail="Service unhealthy")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        metrics_data = mgmt_server.metrics.get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


# Authentication endpoints
@app.post("/auth/login")
async def login(request: FastAPIRequest):
    """User login endpoint"""
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        
        # Authenticate user
        user_context = mgmt_server.rbac.authenticate_user(username, password)
        
        if not user_context:
            mgmt_server.metrics.record_auth_attempt("password", False)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate JWT token
        token = mgmt_server.rbac.generate_jwt_token(user_context)
        
        mgmt_server.metrics.record_auth_attempt("password", True)
        
        response = JSONResponse(content={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_context.user_id,
                "username": user_context.username,
                "role": user_context.role.value,
                "organization_id": user_context.organization_id
            }
        })
        
        # Set session cookie
        response.set_cookie(
            "session",
            token,
            max_age=86400,  # 24 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/auth/logout")
async def logout():
    """User logout endpoint"""
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("session")
    return response


# Dashboard endpoint
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: FastAPIRequest):
    """Main dashboard"""
    try:
        user_context = await get_current_user(request)
        
        # Get dashboard data based on user role
        dashboard_data = await _get_dashboard_data(user_context)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user_context,
            "data": dashboard_data
        })
        
    except HTTPException:
        # Redirect to login if not authenticated
        return templates.TemplateResponse("login.html", {"request": request})


async def _get_dashboard_data(user_context) -> Dict[str, Any]:
    """Get dashboard data based on user role"""
    data = {
        "user": {
            "username": user_context.username,
            "role": user_context.role.value,
            "organization_id": user_context.organization_id
        }
    }
    
    # Admin dashboard
    if user_context.role == Role.ADMIN:
        # System stats
        total_users = mgmt_server.db(mgmt_server.db.users.id > 0).count()
        total_orgs = mgmt_server.db(mgmt_server.db.organizations.id > 0).count()
        total_api_keys = mgmt_server.db(mgmt_server.db.api_keys.enabled == True).count()
        
        # Recent usage
        recent_usage = mgmt_server.db(
            mgmt_server.db.token_usage.created_at > datetime.utcnow() - timedelta(days=7)
        ).select(orderby=~mgmt_server.db.token_usage.created_at, limitby=(0, 10))
        
        data.update({
            "system_stats": {
                "total_users": total_users,
                "total_organizations": total_orgs,
                "active_api_keys": total_api_keys
            },
            "recent_usage": [dict(usage) for usage in recent_usage]
        })
    
    # Organization manager dashboard
    elif user_context.role == Role.RESOURCE_MANAGER:
        org_users = mgmt_server.db(
            mgmt_server.db.users.organization_id == user_context.organization_id
        ).count()
        
        org_usage = mgmt_server.db(
            (mgmt_server.db.token_usage.organization_id == user_context.organization_id) &
            (mgmt_server.db.token_usage.created_at > datetime.utcnow() - timedelta(days=30))
        ).select()
        
        total_tokens = sum(usage.waddleai_tokens for usage in org_usage)
        
        data.update({
            "organization_stats": {
                "total_users": org_users,
                "monthly_token_usage": total_tokens
            },
            "organization_usage": [dict(usage) for usage in org_usage[-20:]]
        })
    
    # Reporter dashboard
    elif user_context.role == Role.REPORTER:
        org_usage = mgmt_server.db(
            (mgmt_server.db.token_usage.organization_id == user_context.organization_id) &
            (mgmt_server.db.token_usage.created_at > datetime.utcnow() - timedelta(days=30))
        ).select()
        
        data.update({
            "usage_analytics": [dict(usage) for usage in org_usage]
        })
    
    # User dashboard
    else:
        user_usage = mgmt_server.db(
            (mgmt_server.db.token_usage.user_id == user_context.user_id) &
            (mgmt_server.db.token_usage.created_at > datetime.utcnow() - timedelta(days=30))
        ).select()
        
        user_api_keys = mgmt_server.db(
            mgmt_server.db.api_keys.user_id == user_context.user_id
        ).select()
        
        data.update({
            "personal_usage": [dict(usage) for usage in user_usage],
            "api_keys": [dict(key) for key in user_api_keys]
        })
    
    return data


# API endpoints for management
@app.get("/api/organizations")
async def list_organizations(user_context = Depends(get_current_user)):
    """List organizations (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    orgs = mgmt_server.db(mgmt_server.db.organizations.id > 0).select()
    return {"organizations": [dict(org) for org in orgs]}


@app.post("/api/organizations")
async def create_organization(
    request: FastAPIRequest,
    user_context = Depends(get_current_user)
):
    """Create organization (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        body = await request.json()
        
        org_id = mgmt_server.db.organizations.insert(
            name=body.get("name"),
            description=body.get("description", ""),
            token_quota_daily=body.get("token_quota_daily", 10000),
            token_quota_monthly=body.get("token_quota_monthly", 300000),
            enabled=True
        )
        
        return {"id": org_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(status_code=500, detail="Failed to create organization")


@app.get("/api/users")
async def list_users(user_context = Depends(get_current_user)):
    """List users"""
    # Admin sees all users, others see organization users only
    if mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        users = mgmt_server.db(mgmt_server.db.users.id > 0).select()
    else:
        users = mgmt_server.db(
            mgmt_server.db.users.organization_id == user_context.organization_id
        ).select()
    
    return {"users": [dict(user) for user in users]}


@app.post("/api/users")
async def create_user(
    request: FastAPIRequest,
    user_context = Depends(get_current_user)
):
    """Create user"""
    # Check permissions
    if not (mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE) or
            mgmt_server.rbac.check_permission(user_context, Permission.RESOURCE_MANAGE)):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        body = await request.json()
        
        # Resource managers can only create users in their organization
        org_id = body.get("organization_id")
        if user_context.role == Role.RESOURCE_MANAGER:
            org_id = user_context.organization_id
        
        user_id = mgmt_server.db.users.insert(
            username=body.get("username"),
            email=body.get("email"),
            password_hash=mgmt_server.rbac.hash_password(body.get("password")),
            role=Role(body.get("role", "user")),
            organization_id=org_id,
            enabled=True
        )
        
        return {"id": user_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@app.get("/api/connection_links")
async def list_connection_links(user_context = Depends(get_current_user)):
    """List LLM connection links (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    links = mgmt_server.db(mgmt_server.db.connection_links.id > 0).select()
    return {"connection_links": [dict(link) for link in links]}


@app.post("/api/connection_links")
async def create_connection_link(
    request: FastAPIRequest,
    user_context = Depends(get_current_user)
):
    """Create LLM connection link (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        body = await request.json()
        
        link_id = mgmt_server.db.connection_links.insert(
            name=body.get("name"),
            provider=body.get("provider"),
            endpoint_url=body.get("endpoint_url"),
            api_key=body.get("api_key"),
            model_list=body.get("model_list", []),
            enabled=body.get("enabled", True),
            rate_limits=body.get("rate_limits", {}),
            tls_config=body.get("tls_config", {})
        )
        
        # Reload connectors to pick up new link
        mgmt_server.llm_manager.reload_connectors()
        
        return {"id": link_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Failed to create connection link: {e}")
        raise HTTPException(status_code=500, detail="Failed to create connection link")


@app.get("/api/api_keys")
async def list_api_keys(user_context = Depends(get_current_user)):
    """List API keys based on user role"""
    # Admin sees all, Resource Manager sees org keys, Users see their own
    if mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        keys = mgmt_server.db(mgmt_server.db.api_keys.id > 0).select()
    elif mgmt_server.rbac.check_permission(user_context, Permission.RESOURCE_MANAGE):
        keys = mgmt_server.db(
            mgmt_server.db.api_keys.organization_id == user_context.organization_id
        ).select()
    else:
        keys = mgmt_server.db(
            mgmt_server.db.api_keys.user_id == user_context.user_id
        ).select()
    
    # Don't return actual key hashes
    api_keys = []
    for key in keys:
        key_dict = dict(key)
        key_dict['key_hash'] = '***REDACTED***'
        api_keys.append(key_dict)
    
    return {"api_keys": api_keys}


@app.post("/api/api_keys")
async def create_api_key(
    request: FastAPIRequest,
    user_context = Depends(get_current_user)
):
    """Create API key"""
    try:
        body = await request.json()
        
        # Determine user and organization for new key
        target_user_id = body.get("user_id", user_context.user_id)
        target_org_id = body.get("organization_id", user_context.organization_id)
        
        # Permission checks
        if target_user_id != user_context.user_id:
            if not (mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE) or
                    (mgmt_server.rbac.check_permission(user_context, Permission.RESOURCE_MANAGE) and
                     target_org_id == user_context.organization_id)):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Generate API key
        import secrets
        key_suffix = secrets.token_hex(8)
        api_key = f"wa-{target_user_id}-{key_suffix}"
        
        # Insert into database
        key_id = mgmt_server.db.api_keys.insert(
            key_hash=mgmt_server.rbac.hash_api_key(api_key),
            name=body.get("name", "Unnamed API Key"),
            user_id=target_user_id,
            organization_id=target_org_id,
            permissions=body.get("permissions", []),
            enabled=True,
            rate_limit=body.get("rate_limit", 1000),
            expires_at=datetime.utcnow() + timedelta(days=body.get("expires_days", 365))
        )
        
        return {
            "id": key_id,
            "api_key": api_key,
            "status": "created",
            "message": "Store this key securely - it won't be shown again"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@app.delete("/api/api_keys/{key_id}")
async def delete_api_key(key_id: int, user_context = Depends(get_current_user)):
    """Delete API key"""
    try:
        # Get the key to check permissions
        key = mgmt_server.db(mgmt_server.db.api_keys.id == key_id).select().first()
        if not key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Permission checks
        if key.user_id != user_context.user_id:
            if not (mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE) or
                    (mgmt_server.rbac.check_permission(user_context, Permission.RESOURCE_MANAGE) and
                     key.organization_id == user_context.organization_id)):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Disable instead of delete to preserve audit trail
        mgmt_server.db(mgmt_server.db.api_keys.id == key_id).update(enabled=False)
        
        return {"status": "deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")


@app.get("/api/usage")
async def get_usage_stats(
    user_context = Depends(get_current_user),
    days: int = 30
):
    """Get usage statistics"""
    try:
        # Build query based on user role
        query = mgmt_server.db.token_usage.created_at > datetime.utcnow() - timedelta(days=days)
        
        if user_context.role == Role.ADMIN:
            # Admin sees all usage
            usage_records = mgmt_server.db(query).select()
        elif user_context.role in [Role.RESOURCE_MANAGER, Role.REPORTER]:
            # Org-level users see organization usage
            usage_records = mgmt_server.db(
                query & (mgmt_server.db.token_usage.organization_id == user_context.organization_id)
            ).select()
        else:
            # Regular users see their own usage
            usage_records = mgmt_server.db(
                query & (mgmt_server.db.token_usage.user_id == user_context.user_id)
            ).select()
        
        # Aggregate statistics
        total_tokens = sum(record.waddleai_tokens for record in usage_records)
        total_requests = len(usage_records)
        
        # Group by day
        daily_usage = {}
        for record in usage_records:
            day = record.created_at.date().isoformat()
            if day not in daily_usage:
                daily_usage[day] = {'tokens': 0, 'requests': 0}
            daily_usage[day]['tokens'] += record.waddleai_tokens
            daily_usage[day]['requests'] += 1
        
        # Group by provider
        provider_usage = {}
        for record in usage_records:
            provider = record.provider
            if provider not in provider_usage:
                provider_usage[provider] = {'tokens': 0, 'requests': 0}
            provider_usage[provider]['tokens'] += record.waddleai_tokens
            provider_usage[provider]['requests'] += 1
        
        return {
            "period_days": days,
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "daily_usage": daily_usage,
            "provider_usage": provider_usage,
            "recent_usage": [dict(record) for record in usage_records[-50:]]
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage stats")


@app.get("/api/system/health")
async def system_health(user_context = Depends(get_current_user)):
    """Get system health status (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        health_results = await mgmt_server.health_monitor.check_all()
        return health_results
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# Ollama management endpoints
@app.post("/api/ollama/pull")
async def ollama_pull_model(
    request: FastAPIRequest,
    user_context = Depends(get_current_user)
):
    """Pull model in Ollama (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        body = await request.json()
        model_name = body.get("model")
        
        if not model_name:
            raise HTTPException(status_code=400, detail="Model name required")
        
        # Find Ollama connector
        ollama_connector = None
        for connector in mgmt_server.llm_manager.connectors.values():
            if hasattr(connector, 'pull_model'):
                ollama_connector = connector
                break
        
        if not ollama_connector:
            raise HTTPException(status_code=404, detail="No Ollama connector found")
        
        result = await ollama_connector.pull_model(model_name)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pull Ollama model: {e}")
        raise HTTPException(status_code=500, detail="Failed to pull model")


@app.delete("/api/ollama/models/{model_name}")
async def ollama_remove_model(
    model_name: str,
    user_context = Depends(get_current_user)
):
    """Remove model from Ollama (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        # Find Ollama connector
        ollama_connector = None
        for connector in mgmt_server.llm_manager.connectors.values():
            if hasattr(connector, 'remove_model'):
                ollama_connector = connector
                break
        
        if not ollama_connector:
            raise HTTPException(status_code=404, detail="No Ollama connector found")
        
        result = await ollama_connector.remove_model(model_name)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove Ollama model: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove model")


# MCP server management endpoints
@app.get("/api/mcp/status")
async def mcp_status(user_context = Depends(get_current_user)):
    """Get MCP server status (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    return {
        "running": mgmt_server.mcp_websocket_server is not None,
        "host": mgmt_server.config['mcp_host'],
        "port": mgmt_server.config['mcp_port'],
        "active_clients": len(mgmt_server.mcp_server.clients) if mgmt_server.mcp_server else 0,
        "auto_start": mgmt_server.config['mcp_auto_start']
    }


@app.post("/api/mcp/start")
async def start_mcp_server(user_context = Depends(get_current_user)):
    """Start MCP server (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        if mgmt_server.mcp_websocket_server:
            return {"status": "already_running", "message": "MCP server is already running"}
        
        await mgmt_server.start_mcp_server()
        return {
            "status": "started",
            "message": f"MCP server started on ws://{mgmt_server.config['mcp_host']}:{mgmt_server.config['mcp_port']}"
        }
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start MCP server: {str(e)}")


@app.post("/api/mcp/stop")
async def stop_mcp_server(user_context = Depends(get_current_user)):
    """Stop MCP server (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    try:
        if not mgmt_server.mcp_websocket_server:
            return {"status": "not_running", "message": "MCP server is not running"}
        
        await mgmt_server.stop_mcp_server()
        return {"status": "stopped", "message": "MCP server stopped"}
        
    except Exception as e:
        logger.error(f"Failed to stop MCP server: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop MCP server: {str(e)}")


@app.get("/api/mcp/clients")
async def list_mcp_clients(user_context = Depends(get_current_user)):
    """List active MCP clients (Admin only)"""
    if not mgmt_server.rbac.check_permission(user_context, Permission.ADMIN_MANAGE):
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    if not mgmt_server.mcp_server:
        return {"clients": []}
    
    clients = []
    for websocket, user_ctx in mgmt_server.mcp_server.clients.items():
        clients.append({
            "remote_address": str(websocket.remote_address),
            "user_id": user_ctx.user_id,
            "username": user_ctx.username,
            "role": user_ctx.role.value,
            "organization_id": user_ctx.organization_id
        })
    
    return {"clients": clients}


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )