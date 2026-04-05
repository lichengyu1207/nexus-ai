# -*- coding: utf-8 -*-
"""
Coze工作流API调用服务
用于调用已部署的Coze工作流执行城市数据采集
"""
import asyncio
import json
import logging
import os
import time
import httpx
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CozeAPIError(Exception):
    """Coze API错误"""
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


@dataclass
class CozeWorkflowResult:
    """工作流执行结果"""
    success: bool
    workflow_id: str = ""
    execution_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None


class CozeWorkflowClient:
    """Coze工作流客户端"""
    
    DEFAULT_BASE_URL = "https://mqbpk2ntqq.coze.site"
    
    def __init__(
        self,
        api_token: str = None,
        base_url: str = None,
        timeout: int = 300
    ):
        self.api_token = api_token or os.getenv("COZE_API_TOKEN", "")
        self.base_url = base_url or os.getenv("COZE_BASE_URL", self.DEFAULT_BASE_URL)
        self.timeout = timeout
        
        if self.api_token:
            self.api_token = self.api_token.strip().strip('"').strip("'")
        
        if self.base_url:
            self.base_url = self.base_url.strip().strip('"').strip("'")
        
        if not self.api_token:
            logger.warning("Coze API Token未配置, 请设置COZE_API_TOKEN环境变量")

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def execute_workflow(
        self,
        workflow_id: str = "run",
        params: Dict[str, Any] = None,
        timeout: int = None
    ) -> CozeWorkflowResult:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            params: 工作流参数
            timeout: 超时时间(秒), 建议控制在300秒(5分钟)以内
        
        Returns:
            CozeWorkflowResult: 工作流执行结果
        """
        start_time = time.time()
        timeout = timeout or self.timeout
        params = params or {}
        
        try:
            url = f"{self.base_url}/{workflow_id}"
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=params
                )
                
                duration = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    return CozeWorkflowResult(
                        success=True,
                        workflow_id=workflow_id,
                        data=data,
                        message="工作流执行成功",
                        duration_ms=duration
                    )
                elif response.status_code == 401:
                    error_msg = "认证失败: 缺少或无效的Authorization头"
                    logger.error(error_msg)
                    return CozeWorkflowResult(
                        success=False,
                        workflow_id=workflow_id,
                        message=error_msg,
                        duration_ms=duration,
                        error="UNAUTHORIZED"
                    )
                else:
                    error_msg = f"工作流执行失败: HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", error_msg)
                    except:
                        pass
                    
                    logger.error(error_msg)
                    return CozeWorkflowResult(
                        success=False,
                        workflow_id=workflow_id,
                        message=error_msg,
                        duration_ms=duration,
                        error=f"HTTP_{response.status_code}"
                    )
                    
        except httpx.TimeoutException:
            duration = (time.time() - start_time) * 1000
            error_msg = f"工作流执行超时 (>{timeout}秒)"
            logger.error(error_msg)
            return CozeWorkflowResult(
                success=False,
                workflow_id=workflow_id,
                message=error_msg,
                duration_ms=duration,
                error="TIMEOUT"
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = f"工作流执行异常: {str(e)}"
            logger.error(error_msg)
            return CozeWorkflowResult(
                success=False,
                workflow_id=workflow_id,
                message=error_msg,
                duration_ms=duration,
                error=str(e)
            )

    async def collect_city_data(
        self,
        city: str,
        houses: List[Dict] = None,
        csv_url: str = None
    ) -> CozeWorkflowResult:
        """
        采集城市数据
        
        Args:
            city: 城市名称
            houses: 房源列表(可选)
            csv_url: CSV文件URL(可选)
        
        Returns:
            CozeWorkflowResult: 采集结果
        """
        params = {
            "city": city
        }
        
        if houses:
            params["houses"] = houses
        
        if csv_url:
            params["csv_url"] = csv_url
        
        logger.info(f"开始采集城市数据: {city}")
        
        result = await self.execute_workflow("run", params)
        
        if result.success:
            logger.info(f"城市数据采集成功: {city}, 耗时: {result.duration_ms:.2f}ms")
        else:
            logger.error(f"城市数据采集失败: {city}, 错误: {result.error}")
        
        return result

    async def batch_collect_cities(
        self,
        cities: List[str],
        concurrency: int = 3
    ) -> Dict[str, CozeWorkflowResult]:
        """
        批量采集多个城市数据
        
        Args:
            cities: 城市列表
            concurrency: 并发数
        
        Returns:
            Dict[str, CozeWorkflowResult]: 各城市采集结果
        """
        results = {}
        semaphore = asyncio.Semaphore(concurrency)
        
        async def collect_with_semaphore(city: str):
            async with semaphore:
                result = await self.collect_city_data(city)
                return city, result
        
        tasks = [collect_with_semaphore(city) for city in cities]
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for item in completed:
            if isinstance(item, Exception):
                logger.error(f"批量采集异常: {item}")
            else:
                city, result = item
                results[city] = result
        
        return results


class CityDataCollector:
    """城市数据采集器"""
    
    DEFAULT_CITIES = [
        "长沙", "杭州", "北京", "上海", "深圳",
        "广州", "成都", "武汉", "南京", "重庆"
    ]
    
    def __init__(self, coze_client: CozeWorkflowClient = None):
        self.client = coze_client or CozeWorkflowClient()
        self.cities = self.DEFAULT_CITIES.copy()
        self.last_collection: Dict[str, datetime] = {}
        self.collection_history: List[Dict] = []

    def set_cities(self, cities: List[str]):
        """设置采集城市列表"""
        self.cities = cities
        logger.info(f"已更新采集城市列表: {cities}")

    async def collect_all(self, concurrency: int = 3) -> Dict[str, Any]:
        """采集所有城市数据"""
        start_time = time.time()
        
        logger.info(f"开始批量采集 {len(self.cities)} 个城市数据")
        
        results = await self.client.batch_collect_cities(self.cities, concurrency)
        
        duration = time.time() - start_time
        
        successful = sum(1 for r in results.values() if r.success)
        failed = len(results) - successful
        
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_cities": len(self.cities),
            "successful": successful,
            "failed": failed,
            "duration_seconds": round(duration, 2),
            "results": {
                city: {
                    "success": result.success,
                    "message": result.message,
                    "duration_ms": round(result.duration_ms, 2),
                    "error": result.error
                }
                for city, result in results.items()
            }
        }
        
        self.collection_history.append(summary)
        
        for city in results:
            self.last_collection[city] = datetime.utcnow()
        
        logger.info(f"批量采集完成: 成功 {successful}/{len(self.cities)}, 耗时 {duration:.2f}秒")
        
        return summary

    async def collect_single(self, city: str) -> Dict[str, Any]:
        """采集单个城市数据"""
        result = await self.client.collect_city_data(city)
        
        self.last_collection[city] = datetime.utcnow()
        
        return {
            "city": city,
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "duration_ms": round(result.duration_ms, 2),
            "error": result.error,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_collection_status(self) -> Dict[str, Any]:
        """获取采集状态"""
        return {
            "configured_cities": self.cities,
            "last_collection": {
                city: dt.isoformat() if dt else None
                for city, dt in self.last_collection.items()
            },
            "total_collections": len(self.collection_history),
            "recent_collections": self.collection_history[-5:] if self.collection_history else []
        }


async def run_city_data_collection(
    cities: List[str] = None,
    api_token: str = None
) -> Dict[str, Any]:
    """
    运行城市数据采集
    
    Args:
        cities: 要采集的城市列表, 默认为DEFAULT_CITIES
        api_token: Coze API Token
    
    Returns:
        采集结果摘要
    """
    client = CozeWorkflowClient(api_token=api_token)
    collector = CityDataCollector(client)
    
    if cities:
        collector.set_cities(cities)
    
    return await collector.collect_all()


if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("城市数据采集测试")
        print("=" * 60)
        
        result = await run_city_data_collection(cities=["长沙"])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(main())
