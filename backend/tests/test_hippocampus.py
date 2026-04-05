"""
海马体记忆中枢系统 - 集成测试
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.hippocampus.encoder import memory_encoder, MemoryUnit, MEMORY_TYPE_EPISODIC, MEMORY_TYPE_SEMANTIC
from backend.hippocampus.storage import hippocampus_storage
from backend.hippocampus.retriever import memory_retriever
from backend.hippocampus.manager import memory_manager
from backend.hippocampus.associator import memory_associator


class TestMemoryEncoder:
    def test_encode_basic(self):
        memory = memory_encoder.encode(
            user_id="test_user_1",
            content="我想在深圳买一套三室的房子，预算在500万左右",
            source="consult",
            agents=["supervisor", "analyst"]
        )
        
        assert memory.user_id == "test_user_1"
        assert memory.type == MEMORY_TYPE_EPISODIC
        assert "深圳" in memory.entities
        assert "500万" in memory.entities
        assert memory.importance > 0.3
        assert len(memory.summary) > 0
    
    def test_extract_entities(self):
        entities = memory_encoder.extract_entities(
            "我在北京海淀区看中了一套两居室，价格350万，2024年交房"
        )
        
        assert "北京" in entities
        assert "350万" in entities
        assert "两居" in entities or "两居室" in entities
    
    def test_compute_importance_high(self):
        importance = memory_encoder.compute_importance(
            "这个房子非常重要，是我必须购买的核心资产",
            {"is_decision": True}
        )
        
        assert importance >= 0.5
    
    def test_compute_importance_low(self):
        importance = memory_encoder.compute_importance(
            "随便看看，了解一下市场情况",
            {}
        )
        
        assert importance < 0.5
    
    def test_generate_summary(self):
        long_text = "这是一段很长的文本内容，" * 50
        summary = memory_encoder.generate_summary(long_text, max_length=100)
        
        assert len(summary) <= 103
        assert summary.endswith("...")
    
    def test_encode_preference(self):
        memory = memory_encoder.encode_preference(
            user_id="test_user_2",
            preference="我喜欢南北通透的房子",
            category="户型偏好"
        )
        
        assert memory.type == MEMORY_TYPE_SEMANTIC
        assert memory.importance >= 0.7
        assert memory.context.get("is_preference") == True


class TestMemoryStorage:
    @pytest.mark.asyncio
    async def test_store_and_get(self):
        memory = memory_encoder.encode(
            user_id="test_storage_user",
            content="测试存储功能的记忆内容",
            source="test"
        )
        
        memory_id = await hippocampus_storage.store(memory)
        assert memory_id == memory.id
        
        retrieved = await hippocampus_storage.get(memory_id)
        assert retrieved is not None
        assert retrieved.content == "测试存储功能的记忆内容"
        
        await hippocampus_storage.delete(memory_id)
    
    @pytest.mark.asyncio
    async def test_search(self):
        memory = memory_encoder.encode(
            user_id="test_search_user",
            content="这是一条关于深圳房产的记忆",
            source="test"
        )
        
        await hippocampus_storage.store(memory)
        
        results = await hippocampus_storage.search("test_search_user", "深圳", limit=5)
        assert len(results) > 0
        assert any("深圳" in m.content for m in results)
        
        await hippocampus_storage.delete(memory.id)
    
    @pytest.mark.asyncio
    async def test_search_by_entity(self):
        memory = memory_encoder.encode(
            user_id="test_entity_user",
            content="广州天河区的房价走势分析",
            source="test"
        )
        
        await hippocampus_storage.store(memory)
        
        results = await hippocampus_storage.search_by_entity("test_entity_user", "广州", limit=5)
        assert len(results) > 0
        
        await hippocampus_storage.delete(memory.id)
    
    @pytest.mark.asyncio
    async def test_update_access(self):
        memory = memory_encoder.encode(
            user_id="test_access_user",
            content="测试访问计数",
            source="test"
        )
        
        await hippocampus_storage.store(memory)
        
        await hippocampus_storage.update_access(memory.id)
        
        updated = await hippocampus_storage.get(memory.id)
        assert updated.access_count == 1
        
        await hippocampus_storage.delete(memory.id)


class TestMemoryRetriever:
    @pytest.mark.asyncio
    async def test_retrieve(self):
        memory1 = memory_encoder.encode(
            user_id="test_retrieve_user",
            content="深圳南山区的房价很高，均价超过10万一平",
            source="test"
        )
        memory2 = memory_encoder.encode(
            user_id="test_retrieve_user",
            content="北京朝阳区的商业地产投资机会",
            source="test"
        )
        
        await hippocampus_storage.store(memory1)
        await hippocampus_storage.store(memory2)
        
        results = await memory_retriever.retrieve(
            user_id="test_retrieve_user",
            query="深圳房价",
            limit=5
        )
        
        assert len(results) > 0
        assert any("深圳" in r.memory.content for r in results)
        
        await hippocampus_storage.delete(memory1.id)
        await hippocampus_storage.delete(memory2.id)
    
    @pytest.mark.asyncio
    async def test_retrieve_recent(self):
        memory = memory_encoder.encode(
            user_id="test_recent_user",
            content="最近的记忆测试",
            source="test"
        )
        
        await hippocampus_storage.store(memory)
        
        results = await memory_retriever.retrieve_recent(
            user_id="test_recent_user",
            days=7,
            limit=10
        )
        
        assert len(results) > 0
        
        await hippocampus_storage.delete(memory.id)
    
    @pytest.mark.asyncio
    async def test_get_context_for_prompt(self):
        memory = memory_encoder.encode(
            user_id="test_context_user",
            content="用户偏好南北通透的房子",
            source="preference"
        )
        
        await hippocampus_storage.store(memory)
        
        context = await memory_retriever.get_context_for_prompt(
            user_id="test_context_user",
            query="房子偏好",
            max_memories=5
        )
        
        assert "历史记忆" in context or len(context) > 0
        
        await hippocampus_storage.delete(memory.id)


class TestMemoryAssociator:
    @pytest.mark.asyncio
    async def test_check_entity_overlap(self):
        memory1 = MemoryUnit(
            user_id="test_assoc_user",
            content="深圳南山区房价",
            entities=["深圳", "南山区", "房价"]
        )
        memory2 = MemoryUnit(
            user_id="test_assoc_user",
            content="深圳福田区房价",
            entities=["深圳", "福田区", "房价"]
        )
        
        relation = memory_associator._check_entity_overlap(memory1, memory2)
        
        assert relation is not None
        assert relation[0] == "entity"
        assert relation[1] > 0
    
    @pytest.mark.asyncio
    async def test_check_time_proximity(self):
        memory1 = MemoryUnit(
            user_id="test_time_user",
            content="记忆1",
            timestamp="2026-03-15T10:00:00"
        )
        memory2 = MemoryUnit(
            user_id="test_time_user",
            content="记忆2",
            timestamp="2026-03-15T12:00:00"
        )
        
        relation = memory_associator._check_time_proximity(memory1, memory2)
        
        assert relation is not None
        assert relation[0] == "sequential"


class TestMemoryManager:
    @pytest.mark.asyncio
    async def test_calculate_similarity(self):
        memory1 = MemoryUnit(
            user_id="test_sim_user",
            type="episodic",
            content="深圳南山区的房价分析",
            entities=["深圳", "南山区"]
        )
        memory2 = MemoryUnit(
            user_id="test_sim_user",
            type="episodic",
            content="深圳福田区的房价分析",
            entities=["深圳", "福田区"]
        )
        
        similarity = memory_manager._calculate_similarity(memory1, memory2)
        
        assert similarity > 0.3
    
    @pytest.mark.asyncio
    async def test_get_memory_health(self):
        memory = memory_encoder.encode(
            user_id="test_health_user",
            content="健康度测试记忆",
            source="test"
        )
        
        await hippocampus_storage.store(memory)
        
        health = await memory_manager.get_memory_health("test_health_user")
        
        assert "total_memories" in health
        assert "health_score" in health
        assert health["total_memories"] >= 1
        
        await hippocampus_storage.delete(memory.id)


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        user_id = "test_workflow_user"
        
        memory1 = memory_encoder.encode(
            user_id=user_id,
            content="用户表示喜欢深圳南山区的房子，预算800万",
            source="consult",
            agents=["supervisor"]
        )
        memory2 = memory_encoder.encode(
            user_id=user_id,
            content="用户偏好三室两厅，南北通透",
            source="consult",
            agents=["supervisor"]
        )
        
        id1 = await hippocampus_storage.store(memory1)
        id2 = await hippocampus_storage.store(memory2)
        
        assert id1 is not None
        assert id2 is not None
        
        results = await memory_retriever.retrieve(
            user_id=user_id,
            query="深圳房子偏好",
            limit=5
        )
        
        assert len(results) > 0
        
        context = await memory_retriever.get_context_for_prompt(
            user_id=user_id,
            max_memories=5
        )
        
        assert len(context) > 0
        
        stats = await hippocampus_storage.get_memory_stats(user_id)
        assert stats["total_memories"] >= 2
        
        await hippocampus_storage.delete(id1)
        await hippocampus_storage.delete(id2)
        
        final_stats = await hippocampus_storage.get_memory_stats(user_id)
        assert final_stats["total_memories"] < stats["total_memories"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
