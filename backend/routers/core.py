"""
认知系统核心模块
Cognition System Core Module

提供思维框架、价值体系、决策引擎等核心功能
"""

import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class FrameworkStep:
    """思维框架步骤"""
    def __init__(self, order: int, name: str, description: str, prompt: str = ""):
        self.order = order
        self.name = name
        self.description = description
        self.prompt = prompt


class ThinkingFramework:
    """思维框架"""
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        steps: List[FrameworkStep],
        applicable_scenarios: List[str],
        usage_count: int = 0,
        success_rate: float = 0.5
    ):
        self.id = id
        self.name = name
        self.description = description
        self.steps = steps
        self.applicable_scenarios = applicable_scenarios
        self.usage_count = usage_count
        self.success_rate = success_rate


class ValueType(Enum):
    """价值类型"""
    ETHICAL = "ethical"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    USER_CENTRIC = "user_centric"
    INNOVATION = "innovation"


@dataclass
class ValueProposition:
    """价值主张"""
    id: str
    name: str
    type: ValueType
    statement: str
    explanation: str
    priority: int = 1
    weight: float = 1.0


@dataclass
class DecisionResult:
    """决策结果"""
    decision: str
    confidence: float
    framework_used: str
    thinking_process: List[Dict]
    evaluation: Dict
    alternatives: List[str] = field(default_factory=list)


class CognitionDatabase:
    """认知数据库"""
    
    def __init__(self, db_path: str = "data/cognition.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thinking_frameworks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                steps_json TEXT,
                applicable_scenarios_json TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.5
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS value_propositions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                statement TEXT,
                explanation TEXT,
                priority INTEGER DEFAULT 1,
                weight REAL DEFAULT 1.0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_logs (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                problem TEXT,
                decision_result TEXT,
                framework_used TEXT,
                confidence REAL,
                feedback TEXT,
                feedback_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_cognition (
                agent_id TEXT PRIMARY KEY,
                frameworks_json TEXT,
                values_json TEXT,
                cognitive_bias_json TEXT,
                experience_points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                decision_quality REAL DEFAULT 0.5,
                growth_history_json TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_growth_events (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                event_type TEXT,
                description TEXT,
                experience_gained INTEGER,
                frameworks_unlocked_json TEXT,
                values_refined_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cognitive_analogies (
                id TEXT PRIMARY KEY,
                type TEXT,
                name TEXT,
                source_domain TEXT,
                target_domain TEXT,
                description TEXT,
                mapping_json TEXT,
                lesson TEXT,
                applicable_scenarios_json TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        self._seed_default_data()
    
    def _seed_default_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM thinking_frameworks")
        if cursor.fetchone()[0] == 0:
            default_frameworks = [
                {
                    "id": "first_principles",
                    "name": "第一性原理",
                    "description": "从最基本的事实出发，逐步推导结论",
                    "steps": [
                        {"order": 1, "name": "识别问题", "description": "明确要解决的核心问题"},
                        {"order": 2, "name": "分解问题", "description": "将问题分解为基本组成部分"},
                        {"order": 3, "name": "寻找基本事实", "description": "确定不可再分的基本事实"},
                        {"order": 4, "name": "重新构建", "description": "从基本事实出发重新构建解决方案"}
                    ],
                    "applicable_scenarios": ["problem_solving", "innovation", "analysis"]
                },
                {
                    "id": "six_thinking_hats",
                    "name": "六顶思考帽",
                    "description": "从不同角度全面思考问题",
                    "steps": [
                        {"order": 1, "name": "白帽-客观", "description": "收集客观事实和数据"},
                        {"order": 2, "name": "红帽-情感", "description": "表达直觉和情感反应"},
                        {"order": 3, "name": "黑帽-批判", "description": "指出风险和潜在问题"},
                        {"order": 4, "name": "黄帽-乐观", "description": "发现机会和优势"},
                        {"order": 5, "name": "绿帽-创新", "description": "提出新想法和可能性"},
                        {"order": 6, "name": "蓝帽-控制", "description": "总结和组织思考过程"}
                    ],
                    "applicable_scenarios": ["decision_making", "brainstorming", "evaluation"]
                }
            ]
            
            for fw in default_frameworks:
                cursor.execute("""
                    INSERT INTO thinking_frameworks 
                    (id, name, description, steps_json, applicable_scenarios_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    fw["id"], fw["name"], fw["description"],
                    json.dumps(fw["steps"]), json.dumps(fw["applicable_scenarios"])
                ))
        
        cursor.execute("SELECT COUNT(*) FROM value_propositions")
        if cursor.fetchone()[0] == 0:
            default_values = [
                {"id": "user_first", "name": "用户至上", "type": "user_centric", "statement": "始终以用户需求为核心", "explanation": "所有决策都应优先考虑用户利益", "priority": 1, "weight": 1.0},
                {"id": "quality", "name": "质量优先", "type": "quality", "statement": "追求高质量的产品和服务", "explanation": "质量是长期成功的基础", "priority": 2, "weight": 0.9},
                {"id": "efficiency", "name": "效率导向", "type": "efficiency", "statement": "以最高效的方式完成任务", "explanation": "在保证质量的前提下追求效率", "priority": 3, "weight": 0.8}
            ]
            
            for v in default_values:
                cursor.execute("""
                    INSERT INTO value_propositions
                    (id, name, type, statement, explanation, priority, weight)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (v["id"], v["name"], v["type"], v["statement"], v["explanation"], v["priority"], v["weight"]))
        
        conn.commit()
        conn.close()
    
    def get_all_frameworks(self) -> List[ThinkingFramework]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, steps_json, applicable_scenarios_json, usage_count, success_rate FROM thinking_frameworks")
        
        frameworks = []
        for row in cursor.fetchall():
            steps_data = json.loads(row[3]) if row[3] else []
            steps = [FrameworkStep(**s) for s in steps_data]
            frameworks.append(ThinkingFramework(
                id=row[0], name=row[1], description=row[2],
                steps=steps,
                applicable_scenarios=json.loads(row[4]) if row[4] else [],
                usage_count=row[5], success_rate=row[6]
            ))
        
        conn.close()
        return frameworks
    
    def get_frameworks_by_scenario(self, scenario: str) -> List[ThinkingFramework]:
        all_frameworks = self.get_all_frameworks()
        return [fw for fw in all_frameworks if scenario in fw.applicable_scenarios]
    
    def get_framework(self, framework_id: str) -> Optional[ThinkingFramework]:
        frameworks = self.get_all_frameworks()
        for fw in frameworks:
            if fw.id == framework_id:
                return fw
        return None
    
    def update_framework_usage(self, framework_id: str, success: bool):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE thinking_frameworks 
            SET usage_count = usage_count + 1,
                success_rate = (success_rate * usage_count + ?) / (usage_count + 1)
            WHERE id = ?
        """, (1.0 if success else 0.0, framework_id))
        conn.commit()
        conn.close()
    
    def get_all_values(self) -> List[ValueProposition]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, statement, explanation, priority, weight FROM value_propositions ORDER BY priority")
        
        values = []
        for row in cursor.fetchall():
            values.append(ValueProposition(
                id=row[0], name=row[1], type=ValueType(row[2]),
                statement=row[3], explanation=row[4],
                priority=row[5], weight=row[6]
            ))
        
        conn.close()
        return values
    
    def get_agent_cognition(self, agent_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT frameworks_json, values_json, cognitive_bias_json,
                   experience_points, level, decision_quality, growth_history_json
            FROM agent_cognition WHERE agent_id = ?
        """, (agent_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "agent_id": agent_id,
                "frameworks": json.loads(row[0]) if row[0] else [],
                "values": json.loads(row[1]) if row[1] else {},
                "cognitive_bias": json.loads(row[2]) if row[2] else {},
                "experience_points": row[3],
                "level": row[4],
                "decision_quality": row[5],
                "growth_history": json.loads(row[6]) if row[6] else []
            }
        return None


class FrameworkApplier:
    """思维框架应用器"""
    
    def apply(self, framework: ThinkingFramework, problem: str, context: Dict) -> Dict:
        steps_result = []
        
        for step in framework.steps:
            step_result = {
                "order": step.order,
                "name": step.name,
                "description": step.description,
                "analysis": f"应用 '{step.name}' 分析: {problem}",
                "insights": []
            }
            steps_result.append(step_result)
        
        conclusion = f"基于 '{framework.name}' 框架分析，建议采取以下行动..."
        
        return {
            "steps": steps_result,
            "conclusion": conclusion
        }


class ValueEvaluator:
    """价值评估器"""
    
    def __init__(self, cognition_db: CognitionDatabase):
        self.cognition_db = cognition_db
    
    def evaluate(self, options: List[Dict], context: Dict) -> Dict:
        values = self.cognition_db.get_all_values()
        results = []
        best_option = None
        best_score = -1
        
        start_time = time.time()
        
        for option in options:
            score = 0.0
            evaluations = []
            
            for value in values:
                value_score = self._evaluate_against_value(option, value, context)
                weighted_score = value_score * value.weight
                score += weighted_score
                
                evaluations.append({
                    "value_name": value.name,
                    "value_type": value.type.value,
                    "score": value_score,
                    "weighted_score": weighted_score
                })
            
            results.append({
                "option": option,
                "total_score": score,
                "evaluations": evaluations
            })
            
            if score > best_score:
                best_score = score
                best_option = option
        
        return {
            "results": results,
            "best_option": best_option,
            "evaluation_time": time.time() - start_time
        }
    
    def _evaluate_against_value(self, option: Dict, value: ValueProposition, context: Dict) -> float:
        return 0.5 + (hash(str(option) + value.id) % 50) / 100.0


class DecisionEngine:
    """决策引擎"""
    
    def __init__(self, cognition_db: CognitionDatabase):
        self.cognition_db = cognition_db
        self.framework_applier = FrameworkApplier()
    
    def decide(self, problem: str, context: Dict, agent_id: Optional[str] = None) -> DecisionResult:
        frameworks = self.cognition_db.get_all_frameworks()
        
        if frameworks:
            best_framework = max(frameworks, key=lambda f: f.success_rate)
        else:
            best_framework = ThinkingFramework(
                id="default", name="默认框架", description="基础决策框架",
                steps=[FrameworkStep(1, "分析", "分析问题")],
                applicable_scenarios=[]
            )
        
        apply_result = self.framework_applier.apply(best_framework, problem, context)
        
        decision = f"基于分析，建议采取行动: {problem[:50]}..."
        alternatives = ["方案A: 保守策略", "方案B: 激进策略", "方案C: 平衡策略"]
        
        decision_id = str(uuid.uuid4())
        if agent_id:
            self._log_decision(decision_id, agent_id, problem, decision, best_framework.id, 0.75)
        
        return DecisionResult(
            decision=decision,
            confidence=0.75,
            framework_used=best_framework.name,
            thinking_process=apply_result["steps"],
            evaluation={"method": "framework_based", "framework_id": best_framework.id},
            alternatives=alternatives
        )
    
    def _log_decision(self, decision_id: str, agent_id: str, problem: str, decision: str, framework_id: str, confidence: float):
        conn = sqlite3.connect(self.cognition_db.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO decision_logs (id, agent_id, problem, decision_result, framework_used, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (decision_id, agent_id, problem, decision, framework_id, confidence))
        conn.commit()
        conn.close()
    
    def reflect_on_decision(self, agent_id: str, decision_id: str, feedback: str, score: float):
        conn = sqlite3.connect(self.cognition_db.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE decision_logs 
            SET feedback = ?, feedback_score = ?
            WHERE id = ? AND agent_id = ?
        """, (feedback, score, decision_id, agent_id))
        
        exp_gained = int(score * 100)
        cursor.execute("""
            INSERT INTO agent_growth_events 
            (id, agent_id, event_type, description, experience_gained)
            VALUES (?, ?, 'reflection', ?, ?)
        """, (str(uuid.uuid4()), agent_id, f"决策反思: {feedback[:100]}", exp_gained))
        
        cursor.execute("""
            INSERT OR REPLACE INTO agent_cognition 
            (agent_id, experience_points, level, decision_quality)
            VALUES (
                ?,
                COALESCE((SELECT experience_points FROM agent_cognition WHERE agent_id = ?), 0) + ?,
                COALESCE((SELECT level FROM agent_cognition WHERE agent_id = ?), 1),
                (COALESCE((SELECT decision_quality FROM agent_cognition WHERE agent_id = ?), 0.5) * 0.9 + ? * 0.1)
            )
        """, (agent_id, agent_id, exp_gained, agent_id, agent_id, score))
        
        conn.commit()
        conn.close()


cognition_db = CognitionDatabase()
framework_applier = FrameworkApplier()
value_evaluator = ValueEvaluator(cognition_db)
decision_engine = DecisionEngine(cognition_db)
