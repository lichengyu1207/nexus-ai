import uuid
from typing import Dict, Any, List
from app.schemas.task import TaskSpec, SubTaskSpec

class ZhongshuAgent:
    """中书省智能体 - 负责任务规格生成"""
    
    def generate_spec(self, text: str) -> Dict[str, Any]:
        """
        生成任务规格
        
        Args:
            text: 用户输入文本
            
        Returns:
            任务规格字典
        """
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 解析用户输入，提取子任务
        subtasks = self._parse_input(text)
        
        # 构建任务规格
        spec = TaskSpec(
            task_id=task_id,
            task_type=self._determine_task_type(subtasks),
            subtasks=subtasks,
            execution_mode="parallel" if len(subtasks) > 1 else "serial",
            success_criteria="all_subtasks_completed",
            failure_criteria="any_subtask_failed"
        )
        
        return spec.model_dump()
    
    def _parse_input(self, text: str) -> List[SubTaskSpec]:
        """
        解析用户输入，提取子任务
        
        Args:
            text: 用户输入文本
            
        Returns:
            子任务列表
        """
        subtasks = []
        
        # 简单的规则解析，实际项目中可以使用大模型
        if "分析" in text and "学区房" in text:
            subtasks.append(SubTaskSpec(
                id=str(uuid.uuid4()),
                type="房产分析",
                dependencies=[],
                required_agents=["hubu"],
                parameters={"query": text}
            ))
        
        if "政策" in text:
            subtasks.append(SubTaskSpec(
                id=str(uuid.uuid4()),
                type="政策查询",
                dependencies=[],
                required_agents=["libu"],
                parameters={"query": text}
            ))
        
        if "命盘" in text or "算命" in text:
            subtasks.append(SubTaskSpec(
                id=str(uuid.uuid4()),
                type="命理分析",
                dependencies=[],
                required_agents=["libu"],
                parameters={"query": text}
            ))
        
        # 如果没有识别到具体任务，创建一个默认任务
        if not subtasks:
            subtasks.append(SubTaskSpec(
                id=str(uuid.uuid4()),
                type="通用任务",
                dependencies=[],
                required_agents=["hubu"],
                parameters={"query": text}
            ))
        
        return subtasks
    
    def _determine_task_type(self, subtasks: List[SubTaskSpec]) -> str:
        """
        确定任务类型
        
        Args:
            subtasks: 子任务列表
            
        Returns:
            任务类型
        """
        types = [subtask.type for subtask in subtasks]
        
        if len(types) == 1:
            return types[0]
        elif "房产分析" in types:
            return "房产"
        elif "命理分析" in types:
            return "命理"
        else:
            return "复合"
