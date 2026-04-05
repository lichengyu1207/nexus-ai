import os
from datetime import datetime
from typing import Dict, Any, List
from app.models.task import Task, SubTask
from sqlalchemy.orm import Session

class GongbuAgent:
    """工部智能体 - 负责任务报告生成和输出融合"""
    
    def __init__(self, db: Session):
        self.db = db
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_report(self, task_id: str) -> Dict[str, Any]:
        """
        生成任务报告
        
        Args:
            task_id: 任务ID
            
        Returns:
            报告信息
        """
        # 获取任务信息
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "任务不存在"}
        
        # 获取子任务信息
        subtasks = self.db.query(SubTask).filter(SubTask.task_id == task_id).all()
        
        # 生成报告内容
        report_content = self._generate_report_content(task, subtasks)
        
        # 保存报告
        report_path = self._save_report(task_id, report_content)
        
        return {
            "task_id": task_id,
            "report_path": report_path,
            "status": "success"
        }
    
    def _generate_report_content(self, task: Task, subtasks: List[SubTask]) -> str:
        """
        生成报告内容
        
        Args:
            task: 任务对象
            subtasks: 子任务列表
            
        Returns:
            报告内容
        """
        content = f"# 任务报告\n\n"
        content += f"## 任务概览\n"
        content += f"- 任务ID: {task.id}\n"
        content += f"- 任务类型: {task.type}\n"
        content += f"- 状态: {task.status.value}\n"
        content += f"- 创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if task.completed_at:
            content += f"- 完成时间: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if task.total_duration:
            content += f"- 总耗时: {task.total_duration}秒\n"
        
        content += f"- 跟踪ID: {task.trace_id}\n\n"
        
        content += "## 子任务详情\n"
        for i, subtask in enumerate(subtasks, 1):
            content += f"### 子任务 {i}\n"
            content += f"- ID: {subtask.id}\n"
            content += f"- 类型: {subtask.type}\n"
            content += f"- 状态: {subtask.status.value}\n"
            
            if subtask.start_time:
                content += f"- 开始时间: {subtask.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if subtask.end_time:
                content += f"- 结束时间: {subtask.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if subtask.duration:
                content += f"- 耗时: {subtask.duration}秒\n"
            
            if subtask.result:
                content += f"- 结果: {subtask.result}\n"
            
            if subtask.error:
                content += f"- 错误: {subtask.error}\n"
            
            content += "\n"
        
        return content
    
    def _save_report(self, task_id: str, content: str) -> str:
        """
        保存报告文件
        
        Args:
            task_id: 任务ID
            content: 报告内容
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{task_id}_{timestamp}.md"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath
    
    def get_monitoring_data(self) -> Dict[str, Any]:
        """
        获取监控数据
        
        Returns:
            监控数据
        """
        # 模拟监控数据
        return {
            "agents": {
                "zhongshu": {"cpu": 15.2, "memory": 25.3},
                "shangshu": {"cpu": 20.5, "memory": 30.1},
                "hubu": {"cpu": 18.7, "memory": 28.9},
                "libu": {"cpu": 12.3, "memory": 22.5},
                "gongbu": {"cpu": 10.1, "memory": 18.7}
            },
            "task_stats": {
                "total": 100,
                "completed": 85,
                "failed": 15,
                "success_rate": 85.0
            },
            "tool_calls": {
                "http": 120,
                "local": 80,
                "grpc": 50
            },
            "errors": {
                "timeout": 5,
                "permission": 3,
                "other": 7
            }
        }
