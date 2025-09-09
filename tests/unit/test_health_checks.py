"""
Unit tests for health checks system
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from shared.utils.health_checks import (
    HealthChecker, HealthStatus, ComponentHealth, SystemHealth,
    create_health_checker
)


class TestHealthStatus:
    """Test HealthStatus enum"""
    
    def test_health_status_values(self):
        """Test health status enum values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestComponentHealth:
    """Test ComponentHealth dataclass"""
    
    def test_component_health_creation(self):
        """Test ComponentHealth creation"""
        health = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            message="Database connection established",
            response_time_ms=50.0,
            details={"connections": 5}
        )
        
        assert health.name == "database"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "Database connection established"
        assert health.response_time_ms == 50.0
        assert health.details["connections"] == 5
    
    def test_component_health_defaults(self):
        """Test ComponentHealth default values"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY
        )
        
        assert health.message == ""
        assert health.response_time_ms == 0.0
        assert health.details == {}
    
    def test_to_dict(self):
        """Test ComponentHealth to_dict method"""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            response_time_ms=25.5,
            details={"version": "1.0"}
        )
        
        result = health.to_dict()
        assert result["name"] == "test"
        assert result["status"] == "healthy"
        assert result["message"] == "OK"
        assert result["response_time_ms"] == 25.5
        assert result["details"]["version"] == "1.0"


class TestSystemHealth:
    """Test SystemHealth class"""
    
    def test_system_health_creation(self):
        """Test SystemHealth creation"""
        components = [
            ComponentHealth("db", HealthStatus.HEALTHY),
            ComponentHealth("redis", HealthStatus.DEGRADED)
        ]
        
        health = SystemHealth(
            overall_status=HealthStatus.DEGRADED,
            components=components,
            timestamp=datetime.utcnow()
        )
        
        assert health.overall_status == HealthStatus.DEGRADED
        assert len(health.components) == 2
        assert isinstance(health.timestamp, datetime)
    
    def test_to_dict(self):
        """Test SystemHealth to_dict method"""
        timestamp = datetime.utcnow()
        components = [
            ComponentHealth("db", HealthStatus.HEALTHY),
            ComponentHealth("redis", HealthStatus.UNHEALTHY)
        ]
        
        health = SystemHealth(
            overall_status=HealthStatus.DEGRADED,
            components=components,
            timestamp=timestamp
        )
        
        result = health.to_dict()
        assert result["overall_status"] == "degraded"
        assert len(result["components"]) == 2
        assert result["components"][0]["name"] == "db"
        assert result["components"][1]["name"] == "redis"
        assert result["timestamp"] == timestamp.isoformat()


class TestHealthChecker:
    """Test HealthChecker class"""
    
    def test_health_checker_init(self, mock_db):
        """Test health checker initialization"""
        checker = HealthChecker(mock_db)
        assert checker.db == mock_db
        assert isinstance(checker.checks, dict)
        assert len(checker.checks) > 0
    
    @pytest.mark.asyncio
    async def test_check_database_healthy(self, mock_db):
        """Test database health check (healthy)"""
        checker = HealthChecker(mock_db)
        
        # Mock successful database query
        mock_db.executesql = Mock(return_value=[[1]])
        
        health = await checker._check_database()
        
        assert health.name == "database"
        assert health.status == HealthStatus.HEALTHY
        assert "Database connection successful" in health.message
        assert health.response_time_ms > 0
        mock_db.executesql.assert_called_once_with("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_check_database_unhealthy(self, mock_db):
        """Test database health check (unhealthy)"""
        checker = HealthChecker(mock_db)
        
        # Mock database connection failure
        mock_db.executesql = Mock(side_effect=Exception("Connection failed"))
        
        health = await checker._check_database()
        
        assert health.name == "database"
        assert health.status == HealthStatus.UNHEALTHY
        assert "Database connection failed" in health.message
        assert "Connection failed" in health.details["error"]
    
    @pytest.mark.asyncio
    async def test_check_redis_healthy(self, mock_redis_client):
        """Test Redis health check (healthy)"""
        checker = HealthChecker(Mock())
        
        # Mock Redis client
        checker.redis_client = mock_redis_client
        mock_redis_client.ping.return_value = True
        mock_redis_client.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "2.5M",
            "redis_version": "7.0.0"
        }
        
        health = await checker._check_redis()
        
        assert health.name == "redis"
        assert health.status == HealthStatus.HEALTHY
        assert "Redis connection successful" in health.message
        assert health.details["connected_clients"] == 5
        assert health.details["memory_usage"] == "2.5M"
    
    @pytest.mark.asyncio
    async def test_check_redis_unhealthy(self):
        """Test Redis health check (unhealthy)"""
        checker = HealthChecker(Mock())
        
        # Mock Redis connection failure
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Redis down")
        checker.redis_client = mock_redis
        
        health = await checker._check_redis()
        
        assert health.name == "redis"
        assert health.status == HealthStatus.UNHEALTHY
        assert "Redis connection failed" in health.message
        assert "Redis down" in health.details["error"]
    
    @pytest.mark.asyncio
    async def test_check_redis_no_client(self):
        """Test Redis health check (no client configured)"""
        checker = HealthChecker(Mock())
        checker.redis_client = None
        
        health = await checker._check_redis()
        
        assert health.name == "redis"
        assert health.status == HealthStatus.DEGRADED
        assert "Redis not configured" in health.message
    
    @pytest.mark.asyncio
    async def test_check_disk_space_healthy(self):
        """Test disk space health check (healthy)"""
        checker = HealthChecker(Mock())
        
        # Mock shutil.disk_usage
        with patch('shared.utils.health_checks.shutil.disk_usage') as mock_disk:
            mock_disk.return_value = (1000000000, 200000000, 800000000)  # 80% free
            
            health = await checker._check_disk_space()
            
            assert health.name == "disk_space"
            assert health.status == HealthStatus.HEALTHY
            assert health.details["free_space_gb"] == 0.8  # 800MB -> 0.8GB
            assert health.details["used_space_gb"] == 0.2
            assert health.details["free_percentage"] == 80.0
    
    @pytest.mark.asyncio
    async def test_check_disk_space_degraded(self):
        """Test disk space health check (degraded - low space)"""
        checker = HealthChecker(Mock())
        
        # Mock low disk space (15% free)
        with patch('shared.utils.health_checks.shutil.disk_usage') as mock_disk:
            mock_disk.return_value = (1000000000, 850000000, 150000000)  # 15% free
            
            health = await checker._check_disk_space()
            
            assert health.name == "disk_space"
            assert health.status == HealthStatus.DEGRADED
            assert "Low disk space" in health.message
            assert health.details["free_percentage"] == 15.0
    
    @pytest.mark.asyncio
    async def test_check_disk_space_unhealthy(self):
        """Test disk space health check (unhealthy - very low space)"""
        checker = HealthChecker(Mock())
        
        # Mock very low disk space (5% free)
        with patch('shared.utils.health_checks.shutil.disk_usage') as mock_disk:
            mock_disk.return_value = (1000000000, 950000000, 50000000)  # 5% free
            
            health = await checker._check_disk_space()
            
            assert health.name == "disk_space"
            assert health.status == HealthStatus.UNHEALTHY
            assert "Critical disk space" in health.message
            assert health.details["free_percentage"] == 5.0
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_healthy(self):
        """Test memory usage health check (healthy)"""
        checker = HealthChecker(Mock())
        
        # Mock psutil memory usage
        with patch('shared.utils.health_checks.psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(
                total=8000000000,  # 8GB
                available=6000000000,  # 6GB available
                percent=25.0  # 25% used
            )
            
            health = await checker._check_memory_usage()
            
            assert health.name == "memory"
            assert health.status == HealthStatus.HEALTHY
            assert health.details["total_gb"] == 8.0
            assert health.details["available_gb"] == 6.0
            assert health.details["used_percentage"] == 25.0
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_degraded(self):
        """Test memory usage health check (degraded - high usage)"""
        checker = HealthChecker(Mock())
        
        # Mock high memory usage (85%)
        with patch('shared.utils.health_checks.psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(
                total=8000000000,
                available=1200000000,  # 1.2GB available
                percent=85.0  # 85% used
            )
            
            health = await checker._check_memory_usage()
            
            assert health.name == "memory"
            assert health.status == HealthStatus.DEGRADED
            assert "High memory usage" in health.message
            assert health.details["used_percentage"] == 85.0
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_unhealthy(self):
        """Test memory usage health check (unhealthy - critical usage)"""
        checker = HealthChecker(Mock())
        
        # Mock critical memory usage (95%)
        with patch('shared.utils.health_checks.psutil.virtual_memory') as mock_mem:
            mock_mem.return_value = Mock(
                total=8000000000,
                available=400000000,  # 400MB available
                percent=95.0  # 95% used
            )
            
            health = await checker._check_memory_usage()
            
            assert health.name == "memory"
            assert health.status == HealthStatus.UNHEALTHY
            assert "Critical memory usage" in health.message
            assert health.details["used_percentage"] == 95.0
    
    @pytest.mark.asyncio
    async def test_check_connection_links_healthy(self, mock_db):
        """Test connection links health check (healthy)"""
        checker = HealthChecker(mock_db)
        
        # Mock connection links
        mock_links = [
            Mock(id=1, name="OpenAI", provider="openai", enabled=True),
            Mock(id=2, name="Anthropic", provider="anthropic", enabled=True)
        ]
        mock_db.return_value = Mock()
        mock_db.return_value.select = Mock(return_value=mock_links)
        mock_db.connection_links = Mock()
        
        health = await checker._check_connection_links()
        
        assert health.name == "connection_links"
        assert health.status == HealthStatus.HEALTHY
        assert health.details["total_connections"] == 2
        assert health.details["enabled_connections"] == 2
        assert health.details["disabled_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_check_connection_links_degraded(self, mock_db):
        """Test connection links health check (degraded - some disabled)"""
        checker = HealthChecker(mock_db)
        
        # Mock mix of enabled/disabled connections
        mock_links = [
            Mock(id=1, name="OpenAI", provider="openai", enabled=True),
            Mock(id=2, name="Anthropic", provider="anthropic", enabled=False),
            Mock(id=3, name="Ollama", provider="ollama", enabled=True)
        ]
        mock_db.return_value = Mock()
        mock_db.return_value.select = Mock(return_value=mock_links)
        mock_db.connection_links = Mock()
        
        health = await checker._check_connection_links()
        
        assert health.name == "connection_links"
        assert health.status == HealthStatus.DEGRADED
        assert "Some connection links are disabled" in health.message
        assert health.details["enabled_connections"] == 2
        assert health.details["disabled_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_check_connection_links_unhealthy(self, mock_db):
        """Test connection links health check (unhealthy - no connections)"""
        checker = HealthChecker(mock_db)
        
        # Mock no connections
        mock_db.return_value = Mock()
        mock_db.return_value.select = Mock(return_value=[])
        mock_db.connection_links = Mock()
        
        health = await checker._check_connection_links()
        
        assert health.name == "connection_links"
        assert health.status == HealthStatus.UNHEALTHY
        assert "No connection links configured" in health.message
        assert health.details["total_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self, mock_db):
        """Test running all health checks"""
        checker = HealthChecker(mock_db)
        
        # Mock database check
        mock_db.executesql = Mock(return_value=[[1]])
        
        # Mock connection links check
        mock_links = [Mock(enabled=True)]
        mock_db.return_value = Mock()
        mock_db.return_value.select = Mock(return_value=mock_links)
        mock_db.connection_links = Mock()
        
        # Mock system resources
        with patch('shared.utils.health_checks.shutil.disk_usage') as mock_disk, \
             patch('shared.utils.health_checks.psutil.virtual_memory') as mock_mem:
            
            mock_disk.return_value = (1000000000, 200000000, 800000000)  # 80% free
            mock_mem.return_value = Mock(
                total=8000000000,
                available=6000000000,
                percent=25.0
            )
            
            system_health = await checker.run_all_checks()
            
            assert isinstance(system_health, SystemHealth)
            assert system_health.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
            assert len(system_health.components) >= 4  # At least db, disk, memory, links
    
    @pytest.mark.asyncio
    async def test_determine_overall_status_healthy(self, mock_db):
        """Test overall status determination (healthy)"""
        checker = HealthChecker(mock_db)
        
        components = [
            ComponentHealth("db", HealthStatus.HEALTHY),
            ComponentHealth("redis", HealthStatus.HEALTHY),
            ComponentHealth("disk", HealthStatus.HEALTHY)
        ]
        
        status = checker._determine_overall_status(components)
        assert status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_determine_overall_status_degraded(self, mock_db):
        """Test overall status determination (degraded)"""
        checker = HealthChecker(mock_db)
        
        components = [
            ComponentHealth("db", HealthStatus.HEALTHY),
            ComponentHealth("redis", HealthStatus.DEGRADED),  # One degraded
            ComponentHealth("disk", HealthStatus.HEALTHY)
        ]
        
        status = checker._determine_overall_status(components)
        assert status == HealthStatus.DEGRADED
    
    @pytest.mark.asyncio
    async def test_determine_overall_status_unhealthy(self, mock_db):
        """Test overall status determination (unhealthy)"""
        checker = HealthChecker(mock_db)
        
        components = [
            ComponentHealth("db", HealthStatus.HEALTHY),
            ComponentHealth("redis", HealthStatus.UNHEALTHY),  # One unhealthy
            ComponentHealth("disk", HealthStatus.DEGRADED)
        ]
        
        status = checker._determine_overall_status(components)
        assert status == HealthStatus.UNHEALTHY
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, mock_db):
        """Test getting health metrics"""
        checker = HealthChecker(mock_db)
        
        # Mock health check results
        with patch.object(checker, 'run_all_checks') as mock_checks:
            mock_health = SystemHealth(
                overall_status=HealthStatus.HEALTHY,
                components=[
                    ComponentHealth("db", HealthStatus.HEALTHY, response_time_ms=25.0),
                    ComponentHealth("redis", HealthStatus.DEGRADED, response_time_ms=50.0)
                ],
                timestamp=datetime.utcnow()
            )
            mock_checks.return_value = mock_health
            
            metrics = await checker.get_metrics()
            
            assert "health_check_status" in metrics
            assert "health_check_response_time_ms" in metrics
            assert metrics["health_check_status"]["db"] == 1  # Healthy = 1
            assert metrics["health_check_status"]["redis"] == 0.5  # Degraded = 0.5
            assert metrics["health_check_response_time_ms"]["db"] == 25.0
            assert metrics["health_check_response_time_ms"]["redis"] == 50.0


class TestHealthCheckerFactory:
    """Test health checker factory function"""
    
    def test_create_health_checker(self, mock_db):
        """Test creating health checker"""
        redis_client = Mock()
        
        checker = create_health_checker(mock_db, redis_client)
        
        assert isinstance(checker, HealthChecker)
        assert checker.db == mock_db
        assert checker.redis_client == redis_client
    
    def test_create_health_checker_no_redis(self, mock_db):
        """Test creating health checker without Redis"""
        checker = create_health_checker(mock_db)
        
        assert isinstance(checker, HealthChecker)
        assert checker.db == mock_db
        assert checker.redis_client is None