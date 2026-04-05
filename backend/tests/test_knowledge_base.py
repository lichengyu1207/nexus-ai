"""
知识库服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHouseTypeService:
    """户型面积服务测试"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """模拟数据库连接"""
        mock_conn = AsyncMock()
        return mock_conn
    
    @pytest.mark.asyncio
    async def test_get_area_estimate(self, mock_db_connection):
        """测试面积估算"""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            "min_area": 90,
            "max_area": 140,
            "avg_area": 115,
            "common_areas": "[100, 110, 120]"
        }
        mock_db_connection.execute.return_value = mock_cursor
        
        with patch('services.house_type_service.get_db_connection', return_value=mock_db_connection):
            from services.house_type_service import get_area_estimate
            result = await get_area_estimate("3室2厅", "上海")
            
            assert result is not None
            assert result["min_area"] == 90
            assert result["max_area"] == 140
            assert result["avg_area"] == 115
    
    @pytest.mark.asyncio
    async def test_get_area_estimate_not_found(self, mock_db_connection):
        """测试面积估算未找到"""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_db_connection.execute.return_value = mock_cursor
        
        with patch('services.house_type_service.get_db_connection', return_value=mock_db_connection):
            from services.house_type_service import get_area_estimate
            result = await get_area_estimate("10室10厅", "上海")
            
            assert result is None


class TestPriceEstimator:
    """价格估算服务测试"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """模拟数据库连接"""
        mock_conn = AsyncMock()
        return mock_conn
    
    @pytest.mark.asyncio
    async def test_estimate_price(self, mock_db_connection):
        """测试价格估算"""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            "avg_price_per_sqm": 65000,
            "min_price_per_sqm": 50000,
            "max_price_per_sqm": 80000
        }
        mock_db_connection.execute.return_value = mock_cursor
        
        with patch('services.price_estimator.get_db_connection', return_value=mock_db_connection):
            from services.price_estimator import estimate_price
            result = await estimate_price("上海", "浦东新区", 100)
            
            assert result is not None
            assert result["avg_total_price"] == 6500000
            assert result["min_total_price"] == 5000000
            assert result["max_total_price"] == 8000000
    
    @pytest.mark.asyncio
    async def test_get_district_price(self, mock_db_connection):
        """测试区域价格获取"""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            "avg_price_per_sqm": 72000,
            "min_price_per_sqm": 55000,
            "max_price_per_sqm": 90000
        }
        mock_db_connection.execute.return_value = mock_cursor
        
        with patch('services.price_estimator.get_db_connection', return_value=mock_db_connection):
            from services.price_estimator import get_district_price
            result = await get_district_price("北京", "朝阳区")
            
            assert result is not None
            assert result["avg_price_per_sqm"] == 72000


class TestDistrictInfo:
    """区域介绍服务测试"""
    
    @pytest.mark.asyncio
    async def test_get_district_info(self):
        """测试区域介绍获取"""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            "id": "test-id",
            "city": "上海",
            "district": "浦东新区",
            "introduction": "浦东新区是上海的一个重要区域",
            "transportation": "地铁2号线、7号线",
            "education": "有多所重点学校",
            "commercial": "陆家嘴金融中心",
            "future_plan": "继续开发临港新城",
            "pros": '["交通便利", "发展潜力大"]',
            "cons": '["房价较高"]'
        }
        mock_conn.execute.return_value = mock_cursor
        
        with patch('routers.district_info.get_db_connection', return_value=mock_conn):
            from routers.district_info import get_district_info_detail
            result = await get_district_info_detail("上海", "浦东新区")
            
            assert result is not None
            assert result["city"] == "上海"
            assert result["district"] == "浦东新区"


class TestFeedbackSystem:
    """反馈系统测试"""
    
    @pytest.mark.asyncio
    async def test_create_feedback(self):
        """测试创建反馈"""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()
        
        with patch('database.get_db_connection', return_value=mock_conn):
            from database import FeedbackDB
            
            result = await FeedbackDB.create_feedback(
                feedback_id="test-id",
                report_id="report-1",
                user_id="user-1",
                rating=1,
                issues=["price_accuracy"],
                comment="价格不准确",
                contact_allowed=True
            )
            
            assert result["id"] == "test-id"
            assert result["rating"] == 1
    
    @pytest.mark.asyncio
    async def test_get_feedback_stats(self):
        """测试获取反馈统计"""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        
        mock_cursor.fetchone.side_effect = [
            {"count": 100},
            {"avg_rating": 1.75},
        ]
        mock_cursor.fetchall.side_effect = [
            [{"rating": 1, "count": 25}, {"rating": 2, "count": 75}],
            [{"status": "pending", "count": 10}, {"status": "processed", "count": 90}],
            [{"issues": "[\"price_accuracy\"]", "count": 20}],
            [{"count": 15}],
        ]
        mock_conn.execute.return_value = mock_cursor
        
        with patch('database.get_db_connection', return_value=mock_conn):
            from database import FeedbackDB
            
            stats = await FeedbackDB.get_feedback_stats()
            
            assert stats["total"] == 100


class TestABTestSystem:
    """A/B测试系统测试"""
    
    @pytest.mark.asyncio
    async def test_get_user_group(self):
        """测试获取用户分组"""
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"ab_test_group": "treatment"}
        mock_conn.execute.return_value = mock_cursor
        
        with patch('database.get_db_connection', return_value=mock_conn):
            from database import ABTestDB
            
            group = await ABTestDB.get_user_group("user-1")
            assert group == "treatment"
    
    @pytest.mark.asyncio
    async def test_record_metric(self):
        """测试记录指标"""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()
        
        with patch('database.get_db_connection', return_value=mock_conn):
            from database import ABTestDB
            
            await ABTestDB.record_metric(
                metric_id="metric-1",
                experiment_id="exp-1",
                user_id="user-1",
                group_name="treatment",
                metric_type="parse_request",
                metric_value=1.0
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
