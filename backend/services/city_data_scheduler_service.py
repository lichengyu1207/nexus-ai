# -*- coding: utf-8 -*-
"""
城市数据采集调度服务
定时执行城市数据采集工作流
"""
import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CityDataScheduler:
    """城市数据采集调度器"""
    
    DEFAULT_CITIES = [
        "长沙", "杭州", "北京", "上海", "深圳",
        "广州", "成都", "武汉", "南京", "重庆"
    ]
    
    DEFAULT_SCHEDULE = {
        "day": "monday",
        "time": "02:00"
    }
    
    def __init__(self):
        self.cities = self.DEFAULT_CITIES.copy()
        self.schedule_config = self.DEFAULT_SCHEDULE.copy()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._last_run: Optional[datetime] = None
        self._run_count = 0
        self._results: List[Dict] = []

    def configure(self, cities: List[str] = None, schedule: Dict = None):
        """配置调度器"""
        if cities:
            self.cities = cities
            logger.info(f"已配置采集城市: {cities}")
        
        if schedule:
            self.schedule_config.update(schedule)
            logger.info(f"已配置调度时间: {schedule}")

    def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行")
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        logger.info("城市数据采集调度器已启动")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("城市数据采集调度器已停止")

    def _run_scheduler(self):
        """调度器主循环"""
        import schedule
        
        while self._running:
            try:
                schedule.every().monday.at("02:00").do(self._scheduled_task)
                
                while self._running:
                    schedule.run_pending()
                    time.sleep(60)
                    
            except Exception as e:
                logger.error(f"调度器异常: {e}")
                break

    def _scheduled_task(self):
        """执行定时任务"""
        logger.info("开始执行定时采集任务")
        asyncio.run(self._collect_all_cities())

    async def _collect_all_cities(self):
        """采集所有城市数据"""
        from .coze_workflow_client import run_city_data_collection
        
        result = await run_city_data_collection(self.cities)
        
        self._last_run = datetime.utcnow()
        self._run_count += 1
        self._results.append(result)
        
        logger.info(f"采集完成: 成功 {result['successful']}/{result['total_cities']}")
        return result

    async def run_now(self, cities: List[str] = None) -> Dict:
        """立即执行采集"""
        target_cities = cities or self.cities
        
        from .coze_workflow_client import run_city_data_collection
        
        result = await run_city_data_collection(target_cities)
        
        self._last_run = datetime.utcnow()
        self._run_count += 1
        self._results.append(result)
        
        return result

    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "running": self._running,
            "cities": self.cities,
            "schedule": self.schedule_config,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "run_count": self._run_count,
            "recent_results": self._results[-5:] if self._results else []
        }


_scheduler_instance: Optional[CityDataScheduler] = None


def get_scheduler() -> CityDataScheduler:
    """获取调度器单例"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = CityDataScheduler()
    
    return _scheduler_instance


async def setup_city_data_scheduler():
    """设置城市数据采集调度器"""
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("城市数据采集调度器设置完成")


async def shutdown_city_data_scheduler():
    """关闭城市数据采集调度器"""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance.stop()
        _scheduler_instance = None
    
    logger.info("城市数据采集调度器已关闭")


if __name__ == "__main__":
    async def test():
        scheduler = get_scheduler()
        
        result = await scheduler.run_now(["长沙"])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
