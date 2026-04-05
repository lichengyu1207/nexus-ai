"""
通知API测试
测试通知创建、获取、标记已读等功能
"""
import pytest
from httpx import AsyncClient

from database import NotificationDB


class TestNotificationList:
    """通知列表测试"""
    
    @pytest.mark.asyncio
    async def test_get_notifications_unauthorized(self, client: AsyncClient):
        """测试未授权获取通知"""
        response = await client.get("/api/notifications")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_notifications_empty(self, auth_client: AsyncClient):
        """测试空通知列表"""
        response = await auth_client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        assert data["unread_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_notifications_with_data(self, auth_client: AsyncClient):
        """测试有数据的通知列表"""
        import uuid
        user_email = auth_client.headers.get("Authorization", "").split()[-1] if "Authorization" in auth_client.headers else "test"
        
        from database import UserDB
        users = await UserDB.get_all_users()
        user_id = None
        for u in users:
            if u.get("email"):
                user_id = u["id"]
                break
        
        if user_id:
            await NotificationDB.create_notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                notification_type="test",
                content="测试通知",
                title="测试"
            )
        
        response = await auth_client.get("/api/notifications")
        assert response.status_code == 200


class TestUnreadCount:
    """未读数量测试"""
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, auth_client: AsyncClient):
        """测试获取未读数量"""
        response = await auth_client.get("/api/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)


class TestMarkAsRead:
    """标记已读测试"""
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, auth_client: AsyncClient):
        """测试标记单条通知已读"""
        import uuid
        from database import UserDB
        
        users = await UserDB.get_all_users()
        user_id = None
        for u in users:
            if u.get("email"):
                user_id = u["id"]
                break
        
        if user_id:
            notification_id = str(uuid.uuid4())
            await NotificationDB.create_notification(
                notification_id=notification_id,
                user_id=user_id,
                notification_type="test",
                content="测试通知",
                title="测试"
            )
            
            response = await auth_client.put(f"/api/notifications/{notification_id}/read")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, auth_client: AsyncClient):
        """测试标记全部已读"""
        response = await auth_client.put("/api/notifications/read-all")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data


class TestNotificationDelete:
    """通知删除测试"""
    
    @pytest.mark.asyncio
    async def test_delete_notification(self, auth_client: AsyncClient):
        """测试删除通知"""
        import uuid
        from database import UserDB
        
        users = await UserDB.get_all_users()
        user_id = None
        for u in users:
            if u.get("email"):
                user_id = u["id"]
                break
        
        if user_id:
            notification_id = str(uuid.uuid4())
            await NotificationDB.create_notification(
                notification_id=notification_id,
                user_id=user_id,
                notification_type="test",
                content="要删除的通知",
                title="测试"
            )
            
            response = await auth_client.delete(f"/api/notifications/{notification_id}")
            assert response.status_code == 200


class TestNotificationTypes:
    """通知类型测试"""
    
    @pytest.mark.asyncio
    async def test_report_completed_notification(self, auth_client: AsyncClient, test_report: dict):
        """测试报告完成通知"""
        import uuid
        from database import UserDB
        
        users = await UserDB.get_all_users()
        user_id = None
        for u in users:
            if u.get("email"):
                user_id = u["id"]
                break
        
        if user_id:
            await NotificationDB.create_report_completed_notification(
                user_id=user_id,
                report_id=test_report["id"],
                task_id=test_report["task_id"],
                report_title="测试报告"
            )
            
            response = await auth_client.get("/api/notifications")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_mention_notification(self, auth_client: AsyncClient, test_report: dict):
        """测试@提及通知"""
        import uuid
        from database import UserDB
        
        users = await UserDB.get_all_users()
        user_id = None
        for u in users:
            if u.get("email"):
                user_id = u["id"]
                break
        
        if user_id:
            await NotificationDB.create_mention_notification(
                user_id=user_id,
                comment_id=str(uuid.uuid4()),
                report_id=test_report["id"],
                mentioner_name="测试用户"
            )
            
            response = await auth_client.get("/api/notifications")
            assert response.status_code == 200


class TestNotificationFilter:
    """通知过滤测试"""
    
    @pytest.mark.asyncio
    async def test_filter_by_read_status(self, auth_client: AsyncClient):
        """测试按已读状态过滤"""
        response = await auth_client.get("/api/notifications", params={"is_read": False})
        assert response.status_code == 200
        data = response.json()
        for notification in data["notifications"]:
            assert notification["is_read"] is False
    
    @pytest.mark.asyncio
    async def test_pagination(self, auth_client: AsyncClient):
        """测试分页"""
        response = await auth_client.get("/api/notifications", params={"limit": 5, "offset": 0})
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) <= 5
