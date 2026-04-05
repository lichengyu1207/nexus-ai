"""
测试配置文件
提供测试夹具和辅助函数
"""
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from backend.database import init_db, get_db_connection


TEST_DB_PATH = "test_property_ai.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """初始化测试数据库"""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    os.environ["DATABASE_PATH"] = TEST_DB_PATH
    
    await init_db()
    
    yield
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """创建已认证的测试客户端"""
    user_data = {
        "email": "test@example.com",
        "password": "Test123456",
        "full_name": "Test User"
    }
    
    await client.post("/api/auth/register", json=user_data)
    
    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"]
        }
    )
    
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client


@pytest_asyncio.fixture
async def second_user_client(client: AsyncClient) -> AsyncClient:
    """创建第二个用户的测试客户端"""
    user_data = {
        "email": "test2@example.com",
        "password": "Test123456",
        "full_name": "Test User 2"
    }
    
    await client.post("/api/auth/register", json=user_data)
    
    login_response = await client.post(
        "/api/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"]
        }
    )
    
    token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    
    return client


@pytest_asyncio.fixture
async def test_task(auth_client: AsyncClient) -> dict:
    """创建测试任务"""
    task_data = {
        "address": "北京市朝阳区望京街道",
        "property_type": "residential",
        "area": 120,
        "floor": 15,
        "total_floors": 30,
        "orientation": "南北通透",
        "decoration": "精装修",
        "age": 5,
        "purpose": "investment"
    }
    
    response = await auth_client.post("/api/tasks", json=task_data)
    return response.json()


@pytest_asyncio.fixture
async def test_report(auth_client: AsyncClient, test_task: dict) -> dict:
    """创建测试报告"""
    from database import ReportDB
    import uuid
    import json
    
    report_id = str(uuid.uuid4())
    content = {
        "task_id": test_task["id"],
        "style": "balanced",
        "generated_at": "2024-01-01T00:00:00",
        "sections": {
            "summary": {"text": "测试报告摘要"},
            "key_findings": [{"title": "发现1", "description": "描述1", "confidence": 0.9, "source": "test"}]
        },
        "charts": []
    }
    
    await ReportDB.create_report(
        report_id=report_id,
        task_id=test_task["id"],
        user_id=test_task["user_id"],
        content=content,
        summary="测试报告摘要"
    )
    
    await ReportDB.update_status(report_id, "completed")
    
    return {
        "id": report_id,
        "task_id": test_task["id"],
        "user_id": test_task["user_id"],
        "content": content
    }
