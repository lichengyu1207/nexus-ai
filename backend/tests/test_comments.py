"""
评论API测试
测试评论CRUD、回复、@提及等功能
"""
import pytest
from httpx import AsyncClient


class TestCommentCreate:
    """评论创建测试"""
    
    @pytest.mark.asyncio
    async def test_create_comment(self, auth_client: AsyncClient, test_report: dict):
        """测试创建评论"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "这是一条测试评论"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "这是一条测试评论"
        assert data["report_id"] == test_report["id"]
    
    @pytest.mark.asyncio
    async def test_create_comment_unauthorized(self, client: AsyncClient, test_report: dict):
        """测试未授权创建评论"""
        response = await client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "测试评论"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_comment_empty_content(self, auth_client: AsyncClient, test_report: dict):
        """测试空内容评论"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": ""}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_comment_with_mention(self, auth_client: AsyncClient, test_report: dict):
        """测试带@提及的评论"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "这是一条评论 @test_user"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "test_user" in data.get("mentions", [])


class TestCommentList:
    """评论列表测试"""
    
    @pytest.mark.asyncio
    async def test_get_comments_empty(self, auth_client: AsyncClient, test_report: dict):
        """测试空评论列表"""
        response = await auth_client.get(f"/api/reports/{test_report['id']}/comments")
        assert response.status_code == 200
        data = response.json()
        assert "comments" in data
        assert data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_comments_with_data(self, auth_client: AsyncClient, test_report: dict):
        """测试有数据的评论列表"""
        await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "测试评论"}
        )
        
        response = await auth_client.get(f"/api/reports/{test_report['id']}/comments")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["comments"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_comments_nonexistent_report(self, auth_client: AsyncClient):
        """测试获取不存在报告的评论"""
        response = await auth_client.get("/api/reports/nonexistent-id/comments")
        assert response.status_code == 404


class TestCommentReply:
    """评论回复测试"""
    
    @pytest.mark.asyncio
    async def test_create_reply(self, auth_client: AsyncClient, test_report: dict):
        """测试创建回复"""
        comment_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "父评论"}
        )
        parent_id = comment_response.json()["id"]
        
        reply_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "这是一条回复", "parent_id": parent_id}
        )
        assert reply_response.status_code == 200
        data = reply_response.json()
        assert data["parent_id"] == parent_id
    
    @pytest.mark.asyncio
    async def test_get_replies(self, auth_client: AsyncClient, test_report: dict):
        """测试获取回复列表"""
        comment_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "父评论"}
        )
        parent_id = comment_response.json()["id"]
        
        await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "回复1", "parent_id": parent_id}
        )
        await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "回复2", "parent_id": parent_id}
        )
        
        response = await auth_client.get(f"/api/comments/{parent_id}/replies")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    @pytest.mark.asyncio
    async def test_reply_to_nonexistent_comment(self, auth_client: AsyncClient, test_report: dict):
        """测试回复不存在的评论"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "回复", "parent_id": "nonexistent-id"}
        )
        assert response.status_code == 404


class TestCommentUpdate:
    """评论更新测试"""
    
    @pytest.mark.asyncio
    async def test_update_own_comment(self, auth_client: AsyncClient, test_report: dict):
        """测试更新自己的评论"""
        create_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "原始评论"}
        )
        comment_id = create_response.json()["id"]
        
        update_response = await auth_client.put(
            f"/api/comments/{comment_id}",
            json={"content": "更新后的评论"}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["content"] == "更新后的评论"
    
    @pytest.mark.asyncio
    async def test_update_other_user_comment(
        self,
        auth_client: AsyncClient,
        second_user_client: AsyncClient,
        test_report: dict
    ):
        """测试更新其他用户的评论"""
        create_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "用户1的评论"}
        )
        comment_id = create_response.json()["id"]
        
        update_response = await second_user_client.put(
            f"/api/comments/{comment_id}",
            json={"content": "尝试修改"}
        )
        assert update_response.status_code == 403


class TestCommentDelete:
    """评论删除测试"""
    
    @pytest.mark.asyncio
    async def test_delete_own_comment(self, auth_client: AsyncClient, test_report: dict):
        """测试删除自己的评论"""
        create_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "要删除的评论"}
        )
        comment_id = create_response.json()["id"]
        
        delete_response = await auth_client.delete(f"/api/comments/{comment_id}")
        assert delete_response.status_code == 200
        
        list_response = await auth_client.get(f"/api/reports/{test_report['id']}/comments")
        comments = list_response.json()["comments"]
        assert not any(c["id"] == comment_id for c in comments)
    
    @pytest.mark.asyncio
    async def test_delete_other_user_comment(
        self,
        auth_client: AsyncClient,
        second_user_client: AsyncClient,
        test_report: dict
    ):
        """测试删除其他用户的评论"""
        create_response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "用户1的评论"}
        )
        comment_id = create_response.json()["id"]
        
        delete_response = await second_user_client.delete(f"/api/comments/{comment_id}")
        assert delete_response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_comment(self, auth_client: AsyncClient):
        """测试删除不存在的评论"""
        response = await auth_client.delete("/api/comments/nonexistent-id")
        assert response.status_code == 400


class TestMentionExtraction:
    """@提及提取测试"""
    
    @pytest.mark.asyncio
    async def test_single_mention(self, auth_client: AsyncClient, test_report: dict):
        """测试单个@提及"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "@john 请查看这个报告"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "john" in data.get("mentions", [])
    
    @pytest.mark.asyncio
    async def test_multiple_mentions(self, auth_client: AsyncClient, test_report: dict):
        """测试多个@提及"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "@john @jane @bob 请查看"}
        )
        assert response.status_code == 200
        data = response.json()
        mentions = data.get("mentions", [])
        assert "john" in mentions
        assert "jane" in mentions
        assert "bob" in mentions
    
    @pytest.mark.asyncio
    async def test_no_mentions(self, auth_client: AsyncClient, test_report: dict):
        """测试无@提及"""
        response = await auth_client.post(
            f"/api/reports/{test_report['id']}/comments",
            json={"content": "这是一条普通评论"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("mentions") is None or len(data.get("mentions", [])) == 0
