# WaddleAI Integration Guide for Claude Code

## Overview

WaddleAI is an AI proxy and management system that provides OpenAI-compatible APIs with advanced routing, security, and token management. This guide shows how to integrate WaddleAI with your applications and use it through Claude Code.

## Quick Start for Applications

### Using OpenAI-Compatible API

WaddleAI provides a fully compatible OpenAI API that can be used as a drop-in replacement:

```python
import openai

# Configure client to use WaddleAI proxy
client = openai.OpenAI(
    api_key="wa-your-api-key-here",
    base_url="https://your-waddleai-proxy.com/v1"
)

# Use exactly like OpenAI API
response = client.chat.completions.create(
    model="gpt-4",  # Will be routed by WaddleAI
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Using with Different Languages

#### Node.js
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
    apiKey: 'wa-your-api-key-here',
    baseURL: 'https://your-waddleai-proxy.com/v1'
});

const completion = await openai.chat.completions.create({
    messages: [{ role: 'user', content: 'Hello!' }],
    model: 'gpt-4',
});

console.log(completion.choices[0].message.content);
```

#### cURL
```bash
curl https://your-waddleai-proxy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer wa-your-api-key-here" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Management API for Administration

The management server provides comprehensive APIs for system administration:

### Authentication
```python
import requests

# Login to get JWT token
auth_response = requests.post(
    "https://your-waddleai-mgmt.com/auth/login",
    json={
        "username": "admin",
        "password": "your-password"
    }
)
token = auth_response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

### Token Usage Analytics
```python
# Check WaddleAI token usage
usage = requests.get(
    "https://your-waddleai-mgmt.com/analytics/tokens/waddleai",
    headers=headers
).json()

print(f"Total WaddleAI tokens used: {usage['total_waddleai_tokens']}")
print(f"LLM breakdown: {usage['llm_breakdown']}")

# Check specific user usage
user_usage = requests.get(
    "https://your-waddleai-mgmt.com/analytics/tokens/123",
    headers=headers
).json()
```

### Quota Management
```python
# Update user quotas
quota_update = requests.post(
    "https://your-waddleai-mgmt.com/analytics/quotas/user123",
    headers=headers,
    json={
        "monthly_limit": 200000,
        "daily_limit": 20000
    }
)

# Check quota utilization
quotas = requests.get(
    "https://your-waddleai-mgmt.com/analytics/quotas",
    headers=headers
).json()
```

### API Key Management
```python
# Create new API key
new_key = requests.post(
    "https://your-waddleai-mgmt.com/api-keys",
    headers=headers,
    json={
        "name": "Production API Key",
        "expires_days": 90,
        "permissions": {
            "models": ["gpt-4", "claude-3-opus"],
            "rate_limit": 100
        }
    }
).json()

print(f"New API key: {new_key['api_key']}")

# List API keys
keys = requests.get(
    "https://your-waddleai-mgmt.com/api-keys",
    headers=headers
).json()
```

### Organization Management
```python
# Create new organization
org = requests.post(
    "https://your-waddleai-mgmt.com/orgs",
    headers=headers,
    json={
        "name": "Acme Corp",
        "description": "Corporate AI usage",
        "token_quota_monthly": 1000000,
        "token_quota_daily": 100000
    }
).json()

# List organizations (scope depends on role)
orgs = requests.get(
    "https://your-waddleai-mgmt.com/orgs",
    headers=headers
).json()
```

## Role-Based API Usage

WaddleAI implements comprehensive role-based access control:

### Admin
- **Full system access** via management API
- All endpoints and functionality available
- Cross-organization visibility and control

```python
# Admin can access all analytics
system_stats = requests.get(
    "https://your-waddleai-mgmt.com/analytics/system",
    headers=admin_headers
).json()

# Configure security policies
security_config = requests.post(
    "https://your-waddleai-mgmt.com/config/security",
    headers=admin_headers,
    json={
        "policy": "strict",
        "max_prompt_length": 10000,
        "block_injection": True
    }
)
```

### Resource Manager
- **Organization-scoped quota management**
- User management within assigned organizations
- Token limit control for assigned organizations

```python
# Resource managers see only assigned organizations
my_orgs = requests.get(
    "https://your-waddleai-mgmt.com/orgs",
    headers=resource_mgr_headers
).json()

# Update quotas for assigned organization users
quota_update = requests.post(
    "https://your-waddleai-mgmt.com/analytics/quotas/user456",
    headers=resource_mgr_headers,
    json={"monthly_limit": 150000}
)
```

### Reporter
- **Read-only analytics and reporting** for assigned organizations
- Usage trend analysis and reporting
- Security incident reporting

```python
# Reporters can generate detailed usage reports
report = requests.get(
    "https://your-waddleai-mgmt.com/analytics/orgs/123",
    headers=reporter_headers,
    params={
        "period": "monthly",
        "include_users": True,
        "format": "detailed"
    }
).json()

# Security threat analytics
security_report = requests.get(
    "https://your-waddleai-mgmt.com/analytics/security",
    headers=reporter_headers
).json()
```

### User
- **OpenAI-compatible API access only**
- Personal API key management
- Own usage statistics

```python
# Users can check their own usage
my_usage = requests.get(
    "https://your-waddleai-proxy.com/api/usage",
    headers={"Authorization": f"Bearer {user_api_key}"}
).json()

# Check remaining quota
quota = requests.get(
    "https://your-waddleai-proxy.com/api/quota",
    headers={"Authorization": f"Bearer {user_api_key}"}
).json()

print(f"Daily remaining: {quota['daily']['remaining']}")
print(f"Monthly remaining: {quota['monthly']['remaining']}")
```

## Dual Token System

WaddleAI uses a sophisticated dual token system for accurate billing and analytics:

### WaddleAI Tokens
- **Normalized billing units** across all LLM providers
- Used for quota enforcement and cost calculation
- Consistent pricing regardless of underlying LLM

### LLM Tokens  
- **Raw provider token counts** (input/output)
- Used for detailed analytics and optimization
- Provider-specific insights and debugging

```python
# Usage response includes both token types
{
    "usage": {
        "prompt_tokens": 100,      # Raw LLM input tokens
        "completion_tokens": 50,   # Raw LLM output tokens
        "total_tokens": 150,       # Total LLM tokens
        "waddleai_tokens": 15      # Normalized WaddleAI tokens
    }
}

# Detailed analytics show breakdown
{
    "total_waddleai_tokens": 1500,
    "llm_breakdown": {
        "openai_gpt4": {"input": 8000, "output": 4000},
        "anthropic_claude": {"input": 3000, "output": 1500},
        "ollama_llama2": {"input": 12000, "output": 8000}
    }
}
```

## Advanced Features

### Model Routing
```python
# WaddleAI automatically routes based on your configuration
response = client.chat.completions.create(
    model="smart-router",  # Uses routing LLM to select best model
    messages=[{"role": "user", "content": "Complex reasoning task..."}]
)

# Force specific provider
response = client.chat.completions.create(
    model="ollama:llama2",  # Route to specific Ollama model
    messages=[{"role": "user", "content": "Local processing needed"}]
)
```

### Memory Integration
```python
# Enable conversation memory
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Remember my preferences"}],
    extra_headers={
        "X-WaddleAI-Memory": "user-session-123",
        "X-WaddleAI-Memory-Type": "conversation"
    }
)
```

### Security Features
WaddleAI automatically scans all prompts for security threats:

- **Prompt injection detection**
- **Jailbreak attempt prevention**  
- **Data extraction blocking**
- **Credential harvesting protection**

Security events are logged and can be monitored:

```python
# Check recent security alerts (admin/reporter only)
alerts = requests.get(
    "https://your-waddleai-proxy.com/api/security/threats",
    headers=headers
).json()
```

## Health Monitoring

### Proxy Server Health
```bash
# Kubernetes-style health check
curl https://your-waddleai-proxy.com/healthz

# Detailed status
curl https://your-waddleai-proxy.com/api/status
```

### Prometheus Metrics
```bash
# Get all metrics for monitoring
curl https://your-waddleai-proxy.com/metrics
curl https://your-waddleai-mgmt.com/metrics
```

## Configuration Examples

### Environment Variables
```bash
# Proxy Server
export PROXY_HOST=0.0.0.0
export PROXY_PORT=8000
export DATABASE_URL=postgresql://user:pass@localhost/waddleai
export JWT_SECRET=your-jwt-secret
export SECURITY_POLICY=balanced
export MAX_CONCURRENT_REQUESTS=100

# Management Server  
export MGMT_HOST=0.0.0.0
export MGMT_PORT=8001
export ADMIN_PASSWORD=secure-admin-password
```

### Docker Compose
```yaml
version: '3.8'
services:
  waddleai-proxy:
    build: ./proxy
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/waddleai
      - MANAGEMENT_SERVER_URL=http://waddleai-mgmt:8001
    depends_on:
      - db
      - waddleai-mgmt

  waddleai-mgmt:
    build: ./management
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/waddleai
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=waddleai
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Error Handling

### Common Error Codes
- `401` - Invalid or expired API key/token
- `403` - Insufficient permissions for operation
- `429` - Rate limit or quota exceeded
- `400` - Blocked by security scanning
- `503` - Service temporarily unavailable

### Example Error Response
```json
{
    "error": {
        "type": "quota_exceeded",
        "message": "Daily token quota exceeded",
        "details": {
            "daily_used": 10000,
            "daily_limit": 10000,
            "monthly_used": 150000,
            "monthly_limit": 200000
        }
    }
}
```

## Best Practices

### API Key Security
- Use environment variables for API keys
- Rotate keys regularly  
- Use minimal required permissions
- Monitor usage patterns

### Performance Optimization
- Implement connection pooling
- Cache frequently used data
- Monitor response times
- Use appropriate models for tasks

### Cost Management
- Monitor WaddleAI token consumption
- Set appropriate quotas
- Use cheaper models when possible
- Implement usage alerts

## Support

For additional help:
- Check the full documentation at `/docs/`
- Review troubleshooting guides
- Monitor health endpoints
- Check security logs for issues

---

*This guide covers the core integration patterns for WaddleAI. For complete API documentation, see the full documentation site.*