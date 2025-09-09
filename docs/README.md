# WaddleAI Documentation

WaddleAI is a comprehensive AI proxy and management system that provides OpenAI-compatible APIs with advanced routing, security, and token management capabilities.

## Features

- **OpenAI-Compatible API** - Drop-in replacement for OpenAI API
- **Multi-LLM Support** - Route to OpenAI, Anthropic, Ollama, and more
- **Role-Based Access Control** - Admin, Resource Manager, Reporter, User roles
- **Dual Token System** - WaddleAI tokens for billing, LLM tokens for analytics
- **Security Scanning** - Prompt injection and jailbreak detection
- **Token Management** - Quota enforcement and usage tracking
- **Multi-Tenant** - Organization-based isolation
- **Monitoring** - Prometheus metrics and health checks
- **Memory Integration** - Conversation memory with mem0/ChromaDB

## Architecture

WaddleAI consists of two main components:

- **Proxy Server** - Stateless API gateway with routing and security
- **Management Server** - Configuration portal and state management

## Quick Start

### Using the OpenAI-Compatible API

```python
import openai

client = openai.OpenAI(
    api_key="wa-your-api-key-here",
    base_url="https://your-waddleai-proxy.com/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Managing the System

Access the management portal at `https://your-waddleai-mgmt.com` or use the Management API:

```python
import requests

# Login
auth = requests.post("/auth/login", json={
    "username": "admin", "password": "password"
})
token = auth.json()["access_token"]

# Get usage stats
usage = requests.get("/analytics/usage", 
    headers={"Authorization": f"Bearer {token}"}
).json()
```

## Documentation Structure

- **[Claude Integration](CLAUDE.md)** - Integration guide for applications
- **[Getting Started](getting-started/)** - Installation and setup
- **[API Reference](api/)** - Complete API documentation
- **[Administration](administration/)** - User and system management
- **[Deployment](deployment/)** - Production deployment guides
- **[Integrations](integrations/)** - LLM provider setup
- **[Troubleshooting](troubleshooting/)** - Common issues and solutions

## Roles and Permissions

- **Admin** - Full system access and configuration
- **Resource Manager** - Token quota management for assigned organizations
- **Reporter** - Usage analytics and reporting for assigned organizations
- **User** - Basic API access and personal usage tracking

## Token System

WaddleAI uses a dual token system:

- **WaddleAI Tokens** - Normalized units for billing and quotas
- **LLM Tokens** - Raw provider tokens for detailed analytics

## Security

- Prompt injection detection and blocking
- Role-based access control with organization isolation
- API key authentication with scoped permissions
- Request rate limiting and quota enforcement
- Comprehensive audit logging

## Support

- Health checks: `/healthz` and `/api/status`
- Metrics: `/metrics` (Prometheus format)
- Logs: Structured JSON logging
- Documentation: This documentation site

---

**Ready to get started?** Check out the [installation guide](getting-started/installation.md) or the [Claude integration guide](CLAUDE.md).