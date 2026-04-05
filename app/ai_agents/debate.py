"""
DebateManager - 辩论管理器
负责管理代理间的辩论会话，记录和汇总不同观点
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from collections import defaultdict


class DebateTurn:
    """辩论回合"""
    
    def __init__(
        self,
        session_id: str,
        agent_name: str,
        content: str,
        turn_number: int
    ):
        self.id = str(uuid.uuid4())
        self.session_id = session_id
        self.agent_name = agent_name
        self.content = content
        self.turn_number = turn_number
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "content": self.content,
            "turn_number": self.turn_number,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DebateSession:
    """辩论会话"""
    
    def __init__(
        self,
        task_id: str,
        topic: str,
        participants: List[str]
    ):
        self.id = str(uuid.uuid4())
        self.task_id = task_id
        self.topic = topic
        self.participants = participants
        self.turns: List[DebateTurn] = []
        self.started_at = datetime.utcnow()
        self.ended_at: Optional[datetime] = None
        self.status = "active"  # active, completed
        self.current_turn = 0
        self.max_turns = 3  # 每个代理最多发言3次
    
    def add_turn(self, agent_name: str, content: str) -> DebateTurn:
        """添加发言回合"""
        turn = DebateTurn(
            session_id=self.id,
            agent_name=agent_name,
            content=content,
            turn_number=len(self.turns) + 1
        )
        self.turns.append(turn)
        self.current_turn = len(self.turns)
        return turn
    
    def end_debate(self):
        """结束辩论"""
        self.ended_at = datetime.utcnow()
        self.status = "completed"
    
    def is_completed(self) -> bool:
        """检查辩论是否完成"""
        # 检查是否所有代理都已发言max_turns次
        turn_counts = defaultdict(int)
        for turn in self.turns:
            turn_counts[turn.agent_name] += 1
        
        for participant in self.participants:
            if turn_counts[participant] < self.max_turns:
                return False
        
        return True
    
    def get_current_speaker(self) -> Optional[str]:
        """获取当前应该发言的代理"""
        if self.is_completed():
            return None
        
        # 计算每个代理的发言次数
        turn_counts = defaultdict(int)
        for turn in self.turns:
            turn_counts[turn.agent_name] += 1
        
        # 找到发言次数最少的代理
        min_turns = min(turn_counts.get(p, 0) for p in self.participants)
        
        for participant in self.participants:
            if turn_counts.get(participant, 0) == min_turns:
                return participant
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "topic": self.topic,
            "participants": self.participants,
            "turns": [turn.to_dict() for turn in self.turns],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns
        }


class DebateManager:
    """
    辩论管理器 - 单例模式
    负责管理代理间的辩论会话
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化辩论管理器"""
        if self._initialized:
            return
        
        self._initialized = True
        # 辩论会话存储：{task_id: [sessions]}
        self._sessions: Dict[str, List[DebateSession]] = defaultdict(list)
        # 会话ID到会话的映射
        self._session_map: Dict[str, DebateSession] = {}
        
        print("✅ DebateManager initialized")
    
    def start_debate(
        self,
        task_id: str,
        topic: str,
        participants: List[str]
    ) -> DebateSession:
        """
        创建辩论会话
        
        Args:
            task_id: 任务ID
            topic: 辩论主题
            participants: 参与者列表
            
        Returns:
            DebateSession: 辩论会话对象
        """
        session = DebateSession(
            task_id=task_id,
            topic=topic,
            participants=participants
        )
        
        self._sessions[task_id].append(session)
        self._session_map[session.id] = session
        
        print(f"✅ Debate started: {topic} (Task: {task_id}, Participants: {participants})")
        return session
    
    def add_turn(
        self,
        session_id: str,
        agent_name: str,
        content: str
    ) -> Optional[DebateTurn]:
        """
        添加辩论发言
        
        Args:
            session_id: 会话ID
            agent_name: 代理名称
            content: 发言内容
            
        Returns:
            DebateTurn: 辩论回合对象
        """
        session = self._session_map.get(session_id)
        if not session:
            print(f"❌ Session not found: {session_id}")
            return None
        
        if session.status != "active":
            print(f"❌ Session is not active: {session_id}")
            return None
        
        turn = session.add_turn(agent_name, content)
        print(f"✅ Debate turn added: {agent_name} in session {session_id}")
        
        # 检查是否完成
        if session.is_completed():
            session.end_debate()
            print(f"✅ Debate completed: {session_id}")
        
        return turn
    
    def end_debate(self, session_id: str) -> bool:
        """
        结束辩论
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        session = self._session_map.get(session_id)
        if not session:
            return False
        
        session.end_debate()
        return True
    
    def get_session(self, session_id: str) -> Optional[DebateSession]:
        """
        获取辩论会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            DebateSession: 辩论会话对象
        """
        return self._session_map.get(session_id)
    
    def get_task_debates(self, task_id: str) -> List[DebateSession]:
        """
        获取任务的所有辩论会话
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[DebateSession]: 辩论会话列表
        """
        return self._sessions.get(task_id, [])
    
    def get_transcript(self, session_id: str) -> Dict[str, Any]:
        """
        获取辩论记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 辩论记录
        """
        session = self._session_map.get(session_id)
        if not session:
            return {}
        
        return session.to_dict()
    
    def get_all_transcripts(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务的所有辩论记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict]: 辩论记录列表
        """
        sessions = self.get_task_debates(task_id)
        return [session.to_dict() for session in sessions]
    
    def detect_disagreements(
        self,
        task_id: str,
        agent_outputs: Dict[str, Any],
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        检测代理输出中的分歧
        
        Args:
            task_id: 任务ID
            agent_outputs: 各代理的输出
            threshold: 分歧阈值
            
        Returns:
            List[Dict]: 分歧点列表
        """
        disagreements = []
        
        # 检查价格评估分歧
        if "market_analyst" in agent_outputs and "data_collector" in agent_outputs:
            analyst_data = agent_outputs["market_analyst"]
            collector_data = agent_outputs["data_collector"]
            
            # 比较价格趋势预测
            analyst_trend = analyst_data.get("result", {}).get("market_analysis", {}).get("price_trend", 0)
            collector_trend = collector_data.get("result", {}).get("market_data", {}).get("price_trend", 0)
            
            if abs(analyst_trend - collector_trend) > threshold:
                disagreements.append({
                    "topic": "价格趋势预测",
                    "participants": ["market_analyst", "data_collector"],
                    "description": f"市场分析师预测趋势为{analyst_trend}，数据采集师预测为{collector_trend}",
                    "severity": "medium"
                })
        
        # 检查风险评估分歧
        if "market_analyst" in agent_outputs and "requirement_analyzer" in agent_outputs:
            analyst_risk = agent_outputs["market_analyst"].get("result", {}).get("risk_score", 0.5)
            requirement_risk = agent_outputs["requirement_analyzer"].get("result", {}).get("risk_preference", 0.5)
            
            if abs(analyst_risk - requirement_risk) > threshold:
                disagreements.append({
                    "topic": "风险评估",
                    "participants": ["market_analyst", "requirement_analyzer"],
                    "description": f"市场分析师评估风险为{analyst_risk}，需求分析师偏好为{requirement_risk}",
                    "severity": "high"
                })
        
        return disagreements
    
    def clear_task_debates(self, task_id: str) -> None:
        """
        清除任务的所有辩论记录
        
        Args:
            task_id: 任务ID
        """
        sessions = self._sessions.pop(task_id, [])
        for session in sessions:
            self._session_map.pop(session.id, None)
        
        print(f"✅ Cleared {len(sessions)} debates for task {task_id}")


# 全局单例实例
debate_manager = DebateManager()
