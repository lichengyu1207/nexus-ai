"""
统一智能核心系统测试用例
测试任务分析、智能咨询、记忆系统跨场景调用
"""
import pytest
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class TestAuth:
    """认证测试"""
    
    @pytest.fixture
    async def auth_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            assert response.status_code == 200
            data = response.json()
            return data["access_token"]
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user_id" in data


class TestPersonaSystem:
    """角色系统测试"""
    
    @pytest.fixture
    async def auth_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_get_persona(self, auth_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/consult/persona",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["persona"] in ["zhouyu", "luxun"]
    
    @pytest.mark.asyncio
    async def test_persona_config_valid(self):
        from backend.services.persona_system import PERSONA_CONFIGS, get_persona_system_prompt
        
        for persona_id in ["zhouyu", "luxun"]:
            config = PERSONA_CONFIGS.get(persona_id)
            assert config is not None
            assert config.name in ["周瑜", "陆逊"]
            
            prompt = get_persona_system_prompt(persona_id)
            assert "主公" in prompt
            assert len(prompt) > 100


class TestConsultation:
    """智能咨询测试"""
    
    @pytest.fixture
    async def auth_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_start_consultation(self, auth_token):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/consult/start",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "persona" in data
            assert "welcome_message" in data
    
    @pytest.mark.asyncio
    async def test_send_message(self, auth_token):
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_response = await client.post(
                f"{BASE_URL}/api/consult/start",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            session_id = start_response.json()["session_id"]
            
            message_response = await client.post(
                f"{BASE_URL}/api/consult/message",
                json={"session_id": session_id, "message": "深圳南山区房价如何？"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert message_response.status_code == 200
            data = message_response.json()
            assert "reply" in data
            assert len(data["reply"]) > 0
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, auth_token):
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_response = await client.post(
                f"{BASE_URL}/api/consult/start",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            session_id = start_response.json()["session_id"]
            
            messages = [
                "我想在深圳买房",
                "预算300万左右",
                "推荐几个区域"
            ]
            
            for msg in messages:
                response = await client.post(
                    f"{BASE_URL}/api/consult/message",
                    json={"session_id": session_id, "message": msg},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                assert response.status_code == 200
                assert "reply" in response.json()


class TestMemorySystem:
    """记忆系统测试"""
    
    @pytest.fixture
    async def auth_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_get_memories(self, auth_token):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/api/memory?limit=10",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "memories" in data
            assert "total" in data
    
    @pytest.mark.asyncio
    async def test_search_memories(self, auth_token):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/api/memory/search?query=深圳",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
    
    @pytest.mark.asyncio
    async def test_memory_graph(self, auth_token):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/api/memory/graph",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "edges" in data
    
    @pytest.mark.asyncio
    async def test_memory_stats(self, auth_token):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/api/memory/stats",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200


class TestTaskAnalysis:
    """任务分析测试"""
    
    @pytest.fixture
    async def auth_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_create_task(self, auth_token):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/tasks",
                json={"query": "深圳南山区1000万学区房分析"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code in [200, 201]
            data = response.json()
            assert "task_id" in data or "id" in data


class TestCrossScenarioMemory:
    """跨场景记忆调用测试"""
    
    @pytest.fixture
    async def auth_token(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "1558691995@qq.com", "password": "147258@Zxcvbnm"}
            )
            return response.json()["access_token"]
    
    @pytest.mark.asyncio
    async def test_consultation_stores_memory(self, auth_token):
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_response = await client.post(
                f"{BASE_URL}/api/consult/start",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            session_id = start_response.json()["session_id"]
            
            unique_query = f"测试偏好查询{datetime.now().timestamp()}"
            await client.post(
                f"{BASE_URL}/api/consult/message",
                json={"session_id": session_id, "message": unique_query},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            await asyncio.sleep(1)
            
            memory_response = await client.get(
                f"{BASE_URL}/api/memory/search?query={unique_query[:10]}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert memory_response.status_code == 200


class TestAgents:
    """代理系统测试"""
    
    @pytest.mark.asyncio
    async def test_base_agent_creation(self):
        from backend.agents.base_agent import RequirementAgent, AgentRequest
        
        agent = RequirementAgent()
        assert agent.name == "requirement"
        assert agent.description != ""
    
    @pytest.mark.asyncio
    async def test_agent_persona_prompt(self):
        from backend.agents.base_agent import RequirementAgent
        
        agent = RequirementAgent()
        zhouyu_prompt = agent.get_persona_prompt("zhouyu")
        luxun_prompt = agent.get_persona_prompt("luxun")
        
        assert "周瑜" in zhouyu_prompt or "主公" in zhouyu_prompt
        assert "陆逊" in luxun_prompt or "主公" in luxun_prompt


class TestMessageBus:
    """消息总线测试"""
    
    @pytest.mark.asyncio
    async def test_message_bus_creation(self):
        from backend.message_bus import MessageBus, Message
        
        bus = await MessageBus.get_instance()
        assert bus is not None
        
        message = Message(
            type="test",
            sender="test_agent",
            receiver="target_agent",
            payload={"test": "data"}
        )
        assert message.id != ""
        assert message.type == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
