"""
核心模块单元测试
测试数据库、记忆存储、对话引擎、估值模块等核心功能
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TestDatabase:
    """数据库模块测试"""
    
    @pytest.mark.asyncio
    async def test_get_db_connection(self):
        """测试数据库连接获取"""
        from database import get_db_connection
        
        conn = await get_db_connection()
        assert conn is not None
        
        await conn.close()
    
    @pytest.mark.asyncio
    async def test_get_pool(self):
        """测试连接池获取"""
        from database import get_pool
        
        pool = await get_pool()
        assert pool is not None
    
    @pytest.mark.asyncio
    async def test_abtest_db_compatibility(self):
        """测试AB测试数据库兼容性"""
        from database import ABTestDB
        
        user_group = await ABTestDB.get_user_group("test_user_123")
        assert user_group in ["control", "treatment"]
        
        experiment = await ABTestDB.get_experiment_by_feature("query_parsing")
        assert experiment is None or isinstance(experiment, dict)


class TestMemoryStorage:
    """记忆存储模块测试"""
    
    @pytest.mark.asyncio
    async def test_store_memory(self):
        """测试记忆存储"""
        from memory.storage import MemoryStorage
        
        storage = MemoryStorage()
        
        memory_id = await storage.store(
            user_id="test_user",
            content="测试记忆内容",
            memory_type="short_term",
            importance=0.8
        )
        
        assert memory_id is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_memory(self):
        """测试记忆检索"""
        from memory.storage import MemoryStorage
        
        storage = MemoryStorage()
        
        memories = await storage.retrieve(
            user_id="test_user",
            query="测试",
            limit=10
        )
        
        assert isinstance(memories, list)
    
    @pytest.mark.asyncio
    async def test_memory_pool_singleton(self):
        """测试记忆存储连接池单例"""
        from memory.storage import MemoryStorage
        
        storage1 = MemoryStorage()
        storage2 = MemoryStorage()
        
        assert storage1._pool is storage2._pool


class TestDialogueEngine:
    """对话引擎测试"""
    
    @pytest.mark.asyncio
    async def test_dialogue_initialization(self):
        """测试对话引擎初始化"""
        from services.dialogue_engine import DialogueEngine
        
        engine = DialogueEngine()
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_dialogue_singleton(self):
        """测试对话引擎单例"""
        from services.dialogue_engine import DialogueEngine
        
        assert storage1._pool_instance is storage2._pool_instance


class TestDialogueEngine:
    """对话引擎测试"""
    
    @pytest.mark.asyncio
    async def test_dialogue_initialization(self):
        """测试对话引擎初始化"""
        from services.dialogue_engine import DialogueEngine
        
        engine = DialogueEngine()
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_dialogue_response(self):
        """测试对话响应"""
        from services.dialogue_engine import DialogueEngine
        
        engine = DialogueEngine()
        
        response = await engine.process(
            user_input="你好",
            context={"user_id": "test_user"}
        )
        
        assert response is not None
        assert "text" in response or "response" in response
    
    @pytest.mark.asyncio
    async def test_dialogue_pattern_compilation(self):
        """测试对话模式预编译"""
        from services.dialogue_engine import DialogueEngine
        
        engine = DialogueEngine()
        
        assert hasattr(engine, '_compiled_patterns')
        assert isinstance(engine._compiled_patterns, dict)


class TestPriceEstimator:
    """估值模块测试"""
    
    @pytest.mark.asyncio
    async def test_estimate_price(self):
        """测试价格估算"""
        from services.price_estimator import estimate_price
        
        result = await estimate_price(
            city="深圳",
            district="南山区",
            area_min=100,
            area_max=120,
            house_type="3室2厅",
            special_requirements=["学区房"]
        )
        
        assert result is not None
        assert "total_price" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_city_tier_classification(self):
        """测试城市等级分类"""
        from services.price_estimator import IntelligentPriceEstimator
        
        estimator = IntelligentPriceEstimator()
        
        tier1 = estimator._get_city_tier("北京")
        assert tier1 == "tier1"
        
        tier3 = estimator._get_city_tier("湘潭")
        assert tier3 == "tier3"
    
    @pytest.mark.asyncio
    async def test_price_adjustment(self):
        """测试价格调整系数"""
        from services.price_estimator import IntelligentPriceEstimator
        
        estimator = IntelligentPriceEstimator()
        
        adjustment = estimator._calculate_adjustment(
            house_type="3室2厅",
            special_requirements=["学区房", "近地铁"]
        )
        
        assert adjustment > 1.0


class TestConsultRouter:
    """智能咨询路由测试"""
    
    @pytest.mark.asyncio
    async def test_consult_endpoint(self):
        """测试咨询端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        response = client.post(
            "/api/consult/query",
            json={
                "query": "我想在深圳买一套学区房",
                "user_id": "test_user"
            }
        )
        
        assert response.status_code in [200, 401, 422]


class TestEnhancedHousesRouter:
    """房源查询路由测试"""
    
    @pytest.mark.asyncio
    async def test_houses_search_endpoint(self):
        """测试房源搜索端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        response = client.post(
            "/api/houses/search",
            json={
                "city": "深圳",
                "district": "南山区",
                "room_count": 3
            }
        )
        
        assert response.status_code in [200, 401, 422]


class TestMonitorRouter:
    """监控路由测试"""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        response = client.get("/api/monitor/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_system_metrics(self):
        """测试系统指标端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        response = client.get("/api/monitor/metrics/system")
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard(self):
        """测试监控仪表板端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        response = client.get("/api/monitor/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert "health" in data
        assert "system" in data
        assert "performance" in data


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_memory_storage_performance(self):
        """测试记忆存储性能"""
        import time
        from memory.storage import MemoryStorage
        
        storage = MemoryStorage()
        
        start_time = time.time()
        
        for i in range(10):
            await storage.store(
                user_id=f"test_user_{i}",
                content=f"测试记忆内容 {i}",
                memory_type="short_term",
                importance=0.8
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        assert avg_time < 0.3, f"记忆存储平均响应时间 {avg_time:.3f}s 超过 0.3s 阈值"
    
    @pytest.mark.asyncio
    async def test_dialogue_engine_performance(self):
        """测试对话引擎性能"""
        import time
        from services.dialogue_engine import DialogueEngine
        
        engine = DialogueEngine()
        
        start_time = time.time()
        
        for i in range(10):
            await engine.process(
                user_input="测试对话",
                context={"user_id": f"test_user_{i}"}
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        assert avg_time < 0.3, f"对话引擎平均响应时间 {avg_time:.3f}s 超过 0.3s 阈值"
    
    @pytest.mark.asyncio
    async def test_price_estimator_performance(self):
        """测试估值模块性能"""
        import time
        from services.price_estimator import estimate_price
        
        start_time = time.time()
        
        for i in range(10):
            await estimate_price(
                city="深圳",
                district="南山区",
                area_min=100 + i * 10,
                area_max=120 + i * 10
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        assert avg_time < 0.5, f"估值模块平均响应时间 {avg_time:.3f}s 超过 0.5s 阈值"


def run_tests():
    """运行所有测试"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_tests()
