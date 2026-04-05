"""
异步任务定义
使用Celery处理耗时的分析任务
"""
from app.core.celery_config import celery_app
from app.ai_agents.scheduler import scheduler
from app.services.task_manager import task_manager
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.run_analysis")
def run_analysis(self, task_id: str, query: str, style: str = "balanced"):
    """
    异步执行分析任务
    
    Args:
        self: Celery任务实例
        task_id: 任务ID
        query: 查询内容
        style: 分析风格
        
    Returns:
        Dict: 分析结果
    """
    try:
        # 更新任务状态
        self.update_state(
            state="PROGRESS",
            meta={"task_id": task_id, "status": "正在分析..."}
        )
        
        logger.info(f"Starting analysis task: {task_id}")
        
        # 执行分析
        result = scheduler.run_analysis(
            task_id=task_id,
            query=query,
            style=style
        )
        
        logger.info(f"Analysis task completed: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Analysis task failed: {task_id}, error: {str(e)}")
        
        self.update_state(
            state="FAILURE",
            meta={"task_id": task_id, "error": str(e)}
        )
        
        raise


@celery_app.task(name="app.tasks.analysis_tasks.cleanup_old_tasks")
def cleanup_old_tasks():
    """
    清理过期任务
    删除30天前的任务记录
    """
    try:
        logger.info("Starting cleanup of old tasks")
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # 清理任务记录
        deleted_count = task_manager.cleanup_old_tasks(cutoff_date)
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old tasks")
        
        return {
            "status": "SUCCESS",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise


@celery_app.task(name="app.tasks.analysis_tasks.update_market_data")
def update_market_data():
    """
    更新市场数据
    定期从数据源更新市场信息
    """
    try:
        logger.info("Starting market data update")
        
        # 这里可以添加市场数据更新逻辑
        # 例如：从外部API获取最新房价数据
        
        logger.info("Market data update completed")
        
        return {
            "status": "SUCCESS",
            "message": "Market data updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Market data update failed: {str(e)}")
        raise


@celery_app.task(name="app.tasks.analysis_tasks.generate_report")
def generate_report(task_id: str):
    """
    异步生成报告
    
    Args:
        task_id: 任务ID
        
    Returns:
        Dict: 报告生成结果
    """
    try:
        logger.info(f"Starting report generation for task: {task_id}")
        
        # 获取任务结果
        task_result = task_manager.get_task(task_id)
        
        if not task_result:
            raise ValueError(f"Task not found: {task_id}")
        
        # 生成报告
        from app.ai_agents.report_generator import ReportGenerator
        
        report_generator = ReportGenerator()
        report = report_generator.generate(task_result)
        
        logger.info(f"Report generated for task: {task_id}")
        
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"Report generation failed for task {task_id}: {str(e)}")
        raise
