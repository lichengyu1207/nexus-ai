"""
智能体认知系统
Agent Cognition System

实现思维框架应用、价值评估、决策引擎等核心认知功能
"""
import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ValueType(Enum):
    CORE_VALUE = "core_value"
    JUDGMENT_STANDARD = "judgment_standard"
    PRIORITY = "priority"
    BOTTOM_LINE = "bottom_line"


@dataclass
class ThinkingStep:
    order: int
    name: str
    description: str
    prompt: str
    result: Optional[str] = None


@dataclass
class ThinkingFramework:
    id: str
    name: str
    description: str
    steps: List[ThinkingStep]
    applicable_scenarios: List[str]
    usage_count: int = 0
    success_rate: float = 0.5


@dataclass
class ValueProposition:
    id: str
    name: str
    type: ValueType
    statement: str
    explanation: str
    priority: int
    weight: float


@dataclass
class CognitiveBias:
    time_preference: Dict[str, float] = field(default_factory=lambda: {"past": 0.2, "present": 0.3, "future": 0.5})
    risk_preference: str = "balanced"
    detail_preference: str = "macro_first"
    info_source_preference: str = "data>experience>intuition"
    decision_style: str = "rational"


@dataclass
class DecisionResult:
    decision: str
    confidence: float
    thinking_process: List[Dict]
    evaluation: Dict
    framework_used: str
    alternatives: List[Dict]


class CognitionDatabase:
    """认知系统数据库操作"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "data", "property-ai.db")
        self.db_path = db_path
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_framework(self, framework_id: str) -> Optional[ThinkingFramework]:
        """获取思维框架"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM thinking_frameworks WHERE id = ?", (framework_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_framework(row)
        finally:
            conn.close()
        return None
    
    def get_all_frameworks(self) -> List[ThinkingFramework]:
        """获取所有思维框架"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM thinking_frameworks ORDER BY usage_count DESC")
            return [self._row_to_framework(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_frameworks_by_scenario(self, scenario: str) -> List[ThinkingFramework]:
        """根据场景获取适用的框架"""
        frameworks = self.get_all_frameworks()
        return [fw for fw in frameworks if scenario in fw.applicable_scenarios]
    
    def _row_to_framework(self, row) -> ThinkingFramework:
        steps_data = json.loads(row[3]) if row[3] else []
        steps = [
            ThinkingStep(
                order=s.get("order", idx),
                name=s.get("name", ""),
                description=s.get("description", ""),
                prompt=s.get("prompt", "")
            )
            for idx, s in enumerate(steps_data)
        ]
        return ThinkingFramework(
            id=row[0],
            name=row[1],
            description=row[2],
            steps=steps,
            applicable_scenarios=json.loads(row[4]) if row[4] else [],
            usage_count=row[5] or 0,
            success_rate=row[6] or 0.5
        )
    
    def get_all_values(self) -> List[ValueProposition]:
        """获取所有价值主张"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM value_propositions ORDER BY priority, weight DESC")
            values = []
            for row in cursor.fetchall():
                values.append(ValueProposition(
                    id=row[0],
                    name=row[1],
                    type=ValueType(row[2]),
                    statement=row[3],
                    explanation=row[4],
                    priority=row[5],
                    weight=row[6]
                ))
            return values
        finally:
            conn.close()
    
    def get_agent_cognition(self, agent_id: str) -> Optional[Dict]:
        """获取智能体认知状态"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM agent_cognition WHERE agent_id = ?", (agent_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "agent_id": row[1],
                    "frameworks": json.loads(row[2]) if row[2] else [],
                    "values": json.loads(row[3]) if row[3] else {},
                    "cognitive_bias": json.loads(row[4]) if row[4] else {},
                    "experience_points": row[5] or 0,
                    "level": row[6] or 1,
                    "decision_quality": row[7] or 0.5,
                    "growth_history": json.loads(row[8]) if row[8] else []
                }
        finally:
            conn.close()
        return None
    
    def update_agent_cognition(self, agent_id: str, cognition: Dict):
        """更新智能体认知状态"""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO agent_cognition 
                (id, agent_id, frameworks_json, values_json, cognitive_bias_json, 
                 experience_points, level, decision_quality, growth_history, updated_at)
                VALUES (
                    COALESCE((SELECT id FROM agent_cognition WHERE agent_id = ?), 
                             'cog_' || ?),
                    ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
                )
            """, (
                agent_id, agent_id, agent_id,
                json.dumps(cognition.get("frameworks", [])),
                json.dumps(cognition.get("values", {})),
                json.dumps(cognition.get("cognitive_bias", {})),
                cognition.get("experience_points", 0),
                cognition.get("level", 1),
                cognition.get("decision_quality", 0.5),
                json.dumps(cognition.get("growth_history", []))
            ))
            conn.commit()
        finally:
            conn.close()
    
    def log_decision(self, agent_id: str, decision: DecisionResult, problem: str, context: Dict):
        """记录决策日志"""
        conn = self._get_connection()
        try:
            import uuid
            decision_id = f"dec_{uuid.uuid4().hex[:12]}"
            conn.execute("""
                INSERT INTO decision_logs 
                (id, agent_id, problem, context_json, thinking_process_json, 
                 evaluation_json, decision_result, framework_used, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                decision_id, agent_id, problem,
                json.dumps(context),
                json.dumps(decision.thinking_process),
                json.dumps(decision.evaluation),
                decision.decision,
                decision.framework_used,
                decision.confidence
            ))
            conn.commit()
            return decision_id
        finally:
            conn.close()
    
    def update_framework_usage(self, framework_id: str, success: bool):
        """更新框架使用统计"""
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE thinking_frameworks 
                SET usage_count = usage_count + 1,
                    success_rate = (success_rate * usage_count + ?) / (usage_count + 1),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (1.0 if success else 0.0, framework_id))
            conn.commit()
        finally:
            conn.close()
    
    def add_growth_event(self, agent_id: str, event_type: str, description: str,
                         experience_gained: int = 0, frameworks_unlocked: List[str] = None,
                         values_refined: Dict = None):
        """添加成长事件"""
        conn = self._get_connection()
        try:
            import uuid
            event_id = f"growth_{uuid.uuid4().hex[:12]}"
            conn.execute("""
                INSERT INTO agent_growth_events 
                (id, agent_id, event_type, description, experience_gained, 
                 frameworks_unlocked, values_refined, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                event_id, agent_id, event_type, description,
                experience_gained,
                json.dumps(frameworks_unlocked or []),
                json.dumps(values_refined or {})
            ))
            
            cognition = self.get_agent_cognition(agent_id)
            if cognition:
                cognition["experience_points"] += experience_gained
                new_level = 1 + cognition["experience_points"] // 100
                if new_level > cognition["level"]:
                    cognition["level"] = new_level
                    cognition["growth_history"].append({
                        "type": "level_up",
                        "level": new_level,
                        "timestamp": datetime.now().isoformat()
                    })
                self.update_agent_cognition(agent_id, cognition)
            
            conn.commit()
        finally:
            conn.close()


class FrameworkApplier:
    """思维框架应用器"""
    
    def __init__(self, db: CognitionDatabase = None):
        self.db = db or CognitionDatabase()
    
    def apply(self, framework: ThinkingFramework, problem: str, context: Dict = None) -> Dict:
        """
        应用思维框架分析问题
        
        Returns:
            包含思考过程和结论的字典
        """
        thinking_process = []
        previous_results = []
        
        for step in framework.steps:
            step_prompt = self._build_step_prompt(step, problem, previous_results, context)
            
            step_result = {
                "step": step.name,
                "order": step.order,
                "description": step.description,
                "prompt": step_prompt,
                "thinking": f"[执行{step.name}]",
                "result": None
            }
            
            thinking_process.append(step_result)
            previous_results.append(step_result)
        
        conclusion = self._synthesize_conclusion(thinking_process, problem)
        
        return {
            "framework_id": framework.id,
            "framework_name": framework.name,
            "steps": thinking_process,
            "conclusion": conclusion
        }
    
    def _build_step_prompt(self, step: ThinkingStep, problem: str, 
                          previous_results: List[Dict], context: Dict) -> str:
        """构建步骤提示词"""
        prompt = f"""
请执行思维框架的第{step.order}步：{step.name}

步骤描述：{step.description}

当前问题：{problem}

引导提示：{step.prompt}
"""
        if previous_results:
            prompt += "\n\n已有分析结果：\n"
            for prev in previous_results:
                prompt += f"- {prev['step']}: {prev.get('result', '分析中...')}\n"
        
        if context:
            prompt += f"\n\n上下文信息：{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        return prompt
    
    def _synthesize_conclusion(self, thinking_process: List[Dict], problem: str) -> str:
        """综合思考过程得出结论"""
        return f"基于{len(thinking_process)}步分析，针对'{problem}'得出结论"


class ValueEvaluator:
    """价值评估引擎"""
    
    def __init__(self, db: CognitionDatabase = None):
        self.db = db or CognitionDatabase()
        self.values = self.db.get_all_values()
    
    def evaluate(self, options: List[Dict], context: Dict = None) -> Dict:
        """
        根据价值体系评估选项
        
        Args:
            options: 待评估的选项列表，每个选项包含 name, description 等
            context: 上下文信息
        
        Returns:
            评估结果，包含每个选项的得分和理由
        """
        results = []
        bottom_lines = [v for v in self.values if v.type == ValueType.BOTTOM_LINE]
        core_values = [v for v in self.values if v.type == ValueType.CORE_VALUE]
        priorities = sorted([v for v in self.values if v.type == ValueType.PRIORITY], 
                          key=lambda x: x.priority)
        
        for option in options:
            score = 50.0
            pros = []
            cons = []
            eliminated = False
            
            for bl in bottom_lines:
                if self._check_bottom_line_violation(option, bl, context):
                    eliminated = True
                    cons.append(f"违反底线：{bl.name}")
                    break
            
            if eliminated:
                results.append({
                    "option": option.get("name", "未知选项"),
                    "score": 0,
                    "eliminated": True,
                    "pros": [],
                    "cons": cons,
                    "reasoning": "违反核心底线原则，直接排除"
                })
                continue
            
            for value in core_values:
                alignment = self._check_value_alignment(option, value, context)
                if alignment > 0:
                    score += alignment * value.weight * 20
                    pros.append(f"符合{value.name}")
                elif alignment < 0:
                    score += alignment * value.weight * 20
                    cons.append(f"偏离{value.name}")
            
            for priority in priorities:
                priority_score = self._check_priority_alignment(option, priority, context)
                score += priority_score * priority.weight * 10
            
            score = max(0, min(100, score))
            
            results.append({
                "option": option.get("name", "未知选项"),
                "score": round(score, 1),
                "eliminated": False,
                "pros": pros,
                "cons": cons,
                "reasoning": self._generate_reasoning(option, score, pros, cons)
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "results": results,
            "best_option": results[0] if results else None,
            "evaluation_time": datetime.now().isoformat()
        }
    
    def _check_bottom_line_violation(self, option: Dict, bottom_line: ValueProposition, 
                                     context: Dict) -> bool:
        """检查是否违反底线"""
        option_str = json.dumps(option, ensure_ascii=False).lower()
        keywords = ["纠纷", "问题", "风险", "隐患"]
        return any(kw in option_str for kw in keywords)
    
    def _check_value_alignment(self, option: Dict, value: ValueProposition, 
                               context: Dict) -> float:
        """检查与价值的对齐程度"""
        return 0.3
    
    def _check_priority_alignment(self, option: Dict, priority: ValueProposition, 
                                  context: Dict) -> float:
        """检查与优先级的对齐程度"""
        return 0.0
    
    def _generate_reasoning(self, option: Dict, score: float, 
                          pros: List[str], cons: List[str]) -> str:
        """生成评估理由"""
        if score >= 80:
            return f"高分选项，{len(pros)}个优点，强烈推荐"
        elif score >= 60:
            return f"中等分数，{len(pros)}个优点，可以考虑"
        else:
            return f"低分选项，{len(cons)}个缺点，谨慎选择"


class DecisionEngine:
    """决策引擎"""
    
    def __init__(self, db: CognitionDatabase = None):
        self.db = db or CognitionDatabase()
        self.framework_applier = FrameworkApplier(self.db)
        self.value_evaluator = ValueEvaluator(self.db)
    
    def decide(self, problem: str, context: Dict, agent_id: str = None) -> DecisionResult:
        """
        综合思维框架和价值体系做出决策
        
        Args:
            problem: 问题描述
            context: 上下文信息
            agent_id: 智能体ID（用于获取个性化认知）
        
        Returns:
            决策结果
        """
        cognition = None
        if agent_id:
            cognition = self.db.get_agent_cognition(agent_id)
        
        frameworks = self._select_frameworks(problem, cognition)
        
        if frameworks:
            selected_framework = frameworks[0]
            thinking_result = self.framework_applier.apply(selected_framework, problem, context)
            thinking_process = thinking_result["steps"]
            framework_used = selected_framework.name
        else:
            thinking_process = [{"step": "直接分析", "thinking": "无适用框架，直接分析问题"}]
            framework_used = "default"
        
        options = self._generate_options(problem, thinking_process, context)
        
        evaluation = self.value_evaluator.evaluate(options, context)
        
        if evaluation["best_option"]:
            decision = evaluation["best_option"]["option"]
            confidence = evaluation["best_option"]["score"] / 100
        else:
            decision = "需要更多信息才能做出决策"
            confidence = 0.3
        
        result = DecisionResult(
            decision=decision,
            confidence=confidence,
            thinking_process=thinking_process,
            evaluation=evaluation,
            framework_used=framework_used,
            alternatives=[opt for opt in evaluation["results"][1:4]] if len(evaluation["results"]) > 1 else []
        )
        
        if agent_id:
            self.db.log_decision(agent_id, result, problem, context)
        
        return result
    
    def _select_frameworks(self, problem: str, cognition: Dict = None) -> List[ThinkingFramework]:
        """选择适用的思维框架"""
        scenario = self._detect_scenario(problem)
        
        frameworks = self.db.get_frameworks_by_scenario(scenario)
        
        if not frameworks:
            frameworks = self.db.get_all_frameworks()[:3]
        
        if cognition and cognition.get("frameworks"):
            preferred = cognition["frameworks"]
            frameworks.sort(key=lambda f: preferred.get(f.id, 0), reverse=True)
        
        return frameworks
    
    def _detect_scenario(self, problem: str) -> str:
        """检测问题场景"""
        problem_lower = problem.lower()
        
        if any(kw in problem_lower for kw in ["买房", "购房", "房产", "房子"]):
            return "购房决策"
        elif any(kw in problem_lower for kw in ["投资", "收益", "回报"]):
            return "投资决策"
        elif any(kw in problem_lower for kw in ["风险", "安全", "隐患"]):
            return "风险评估"
        elif any(kw in problem_lower for kw in ["估值", "价值", "价格"]):
            return "房产估值"
        else:
            return "通用分析"
    
    def _generate_options(self, problem: str, thinking_process: List[Dict], 
                         context: Dict) -> List[Dict]:
        """生成候选选项"""
        return [
            {"name": "方案A", "description": "基于分析的推荐方案"},
            {"name": "方案B", "description": "保守型备选方案"},
            {"name": "方案C", "description": "进取型备选方案"}
        ]
    
    def reflect_on_decision(self, agent_id: str, decision_id: str, feedback: str, 
                           feedback_score: float):
        """
        对历史决策进行反思
        
        Args:
            agent_id: 智能体ID
            decision_id: 决策ID
            feedback: 反馈内容
            feedback_score: 反馈评分 (0-1)
        """
        conn = self.db._get_connection()
        try:
            conn.execute("""
                UPDATE decision_logs 
                SET feedback = ?, feedback_score = ?
                WHERE id = ?
            """, (feedback, feedback_score, decision_id))
            conn.commit()
        finally:
            conn.close()
        
        success = feedback_score >= 0.7
        
        cognition = self.db.get_agent_cognition(agent_id)
        if cognition:
            if success:
                self.db.add_growth_event(
                    agent_id, "decision_success",
                    f"决策获得正向反馈，评分：{feedback_score}",
                    experience_gained=10
                )
            else:
                self.db.add_growth_event(
                    agent_id, "decision_review",
                    f"决策获得改进反馈：{feedback}",
                    experience_gained=5
                )


cognition_db = CognitionDatabase()
framework_applier = FrameworkApplier()
value_evaluator = ValueEvaluator()
decision_engine = DecisionEngine()
