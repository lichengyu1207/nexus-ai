# -*- coding: utf-8 -*-
"""
End-to-end tests for consultation module
"""
import pytest
import asyncio
import uuid
import httpx
from unittest.mock import patch, AsyncMock

BASE_URL = "http://localhost:8000"


class TestConsultationE2E:
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_create_session_e2e(self, client):
        response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={
                "initial_message": "我想咨询房产投资",
                "gene_preference": "zhouyu"
            }
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "session_id" in data
        assert data["status"] == "active"
        assert data["gene_name"] == "zhouyu"
    
    @pytest.mark.asyncio
    async def test_send_message_e2e(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "zhouyu"}
        )
        
        session_id = create_response.json()["session_id"]
        
        message_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
            json={"content": "我想在深圳买房，预算300万左右"}
        )
        
        assert message_response.status_code == 200
        data = message_response.json()
        
        assert "message_id" in data
        assert "response" in data
        assert data["persona_used"] == "zhouyu"
    
    @pytest.mark.asyncio
    async def test_get_genes_e2e(self, client):
        response = await client.get(f"{BASE_URL}/api/consult/genes")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 2
        
        gene_names = [g["name"] for g in data]
        assert "zhouyu" in gene_names
        assert "luxun" in gene_names
    
    @pytest.mark.asyncio
    async def test_switch_persona_e2e(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "zhouyu"}
        )
        
        session_id = create_response.json()["session_id"]
        
        switch_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/switch-persona",
            json={"gene_name": "luxun", "weight": 1.0}
        )
        
        assert switch_response.status_code == 200
        data = switch_response.json()
        
        assert data["success"] == True
        assert data["new_persona"] == "luxun"
    
    @pytest.mark.asyncio
    async def test_complete_session_e2e(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "zhouyu"}
        )
        
        session_id = create_response.json()["session_id"]
        
        complete_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/complete",
            params={"rating": 5, "feedback": "非常有帮助"}
        )
        
        assert complete_response.status_code == 200
        assert complete_response.json()["success"] == True
    
    @pytest.mark.asyncio
    async def test_full_consultation_flow_e2e(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={
                "initial_message": "我想咨询房产",
                "gene_preference": "zhouyu"
            }
        )
        
        assert create_response.status_code in [200, 201]
        session_id = create_response.json()["session_id"]
        
        messages = [
            "我想在深圳买房",
            "预算大概300万",
            "主要是自住",
            "请给我详细的分析"
        ]
        
        for msg in messages:
            response = await client.post(
                f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
                json={"content": msg}
            )
            assert response.status_code == 200
        
        complete_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/complete",
            params={"rating": 5}
        )
        
        assert complete_response.status_code == 200


class TestEmotionDetectionE2E:
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_anxious_emotion_handling(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "luxun"}
        )
        
        session_id = create_response.json()["session_id"]
        
        message_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
            json={"content": "我很焦虑，压力很大，不知道该怎么办"}
        )
        
        assert message_response.status_code == 200
        data = message_response.json()
        
        assert "response" in data
        assert len(data["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_persona_auto_switch_on_emotion(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "zhouyu"}
        )
        
        session_id = create_response.json()["session_id"]
        
        message_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
            json={"content": "我非常焦虑，压力很大，睡不着觉"}
        )
        
        assert message_response.status_code == 200


class TestIntentRecognitionE2E:
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_property_intent_recognition(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "zhouyu"}
        )
        
        session_id = create_response.json()["session_id"]
        
        message_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
            json={"content": "我想在深圳买房，预算300万"}
        )
        
        data = message_response.json()
        assert data["intent_detected"] == "property_consultation"
    
    @pytest.mark.asyncio
    async def test_destiny_intent_recognition(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "luxun"}
        )
        
        session_id = create_response.json()["session_id"]
        
        message_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
            json={"content": "帮我算一下八字，我是1990年出生的"}
        )
        
        data = message_response.json()
        assert data["intent_detected"] == "destiny_consultation"
    
    @pytest.mark.asyncio
    async def test_investment_intent_recognition(self, client):
        create_response = await client.post(
            f"{BASE_URL}/api/consult/sessions",
            json={"gene_preference": "zhouyu"}
        )
        
        session_id = create_response.json()["session_id"]
        
        message_response = await client.post(
            f"{BASE_URL}/api/consult/sessions/{session_id}/messages",
            json={"content": "我想投资房产，预算500万，求建议"}
        )
        
        data = message_response.json()
        assert data["intent_detected"] in ["investment_advice", "property_consultation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
