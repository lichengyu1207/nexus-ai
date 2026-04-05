# -*- coding: utf-8 -*-
"""
房都督标准化报告模板系统
生成个人综合决策报告
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ReportSection:
    """报告章节"""
    title: str
    content: str
    subsections: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class PersonalDecisionReport:
    """个人综合决策报告"""
    report_id: str
    generated_at: str
    interpreter: str = "周瑜 & 陆逊"
    
    # 用户核心信息
    user_info: Dict[str, Any] = field(default_factory=dict)
    
    # 六维分析
    six_dimensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 核心建议
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # 行动步骤
    action_steps: List[Dict[str, Any]] = field(default_factory=list)
    
    # 案例参考
    case_references: List[Dict[str, Any]] = field(default_factory=list)
    
    # 免责声明
    disclaimer: str = "本报告基于命理模型与数据分析，仅供参考，最终决策由用户自行负责。"

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """加载报告模板"""
        return {
            "emotion": self._emotion_template(),
            "career": self._career_template(),
            "property": self._property_template(),
            "combined": self._combined_template()
        }
    
    def _emotion_template(self) -> Dict[str, Any]:
        """情感类报告模板"""
        return {
            "title": "房都督 · 情感决策报告",
            "sections": [
                "用户核心信息",
                "问题拆解",
                "六维框架分析",
                "核心建议",
                "可执行步骤",
                "案例参考",
                "免责声明"
            ]
        }
    
    def _career_template(self) -> Dict[str, Any]:
        """事业类报告模板"""
        return {
            "title": "房都督 · 事业决策报告",
            "sections": [
                "用户核心信息",
                "问题拆解",
                "六维框架分析",
                "核心建议",
                "可执行步骤",
                "案例参考",
                "免责声明"
            ]
        }
    
    def _property_template(self) -> Dict[str, Any]:
        """房产类报告模板"""
        return {
            "title": "房都督 · 房产决策报告",
            "sections": [
                "用户核心信息",
                "问题拆解",
                "六维框架分析",
                "房产数据分析",
                "核心建议",
                "可执行步骤",
                "案例参考",
                "免责声明"
            ]
        }
    
    def _combined_template(self) -> Dict[str, Any]:
        """复合类报告模板"""
        return {
            "title": "房都督 · 个人综合决策报告",
            "sections": [
                "用户核心信息",
                "问题拆解",
                "六维框架分析",
                "核心建议",
                "可执行步骤",
                "案例参考",
                "免责声明"
            ]
        }
    
    def generate_report(
        self,
        report_type: str,
        user_info: Dict[str, Any],
        analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        action_steps: List[Dict[str, Any]],
        case_references: List[Dict[str, Any]] = None
    ) -> PersonalDecisionReport:
        """
        生成报告
        
        Args:
            report_type: 报告类型 (emotion/career/property/combined)
            user_info: 用户信息
            analysis: 六维分析结果
            recommendations: 建议列表
            action_steps: 行动步骤
            case_references: 案例参考
        
        Returns:
            PersonalDecisionReport
        """
        import uuid
        
        report = PersonalDecisionReport(
            report_id=f"report_{uuid.uuid4().hex[:8]}",
            generated_at=datetime.now().isoformat(),
            user_info=user_info,
            six_dimensions=analysis,
            recommendations=recommendations,
            action_steps=action_steps,
            case_references=case_references or []
        )
        
        return report
    
    def format_report_markdown(self, report: PersonalDecisionReport) -> str:
        """
        将报告格式化为Markdown
        
        Args:
            report: 报告对象
        
        Returns:
            Markdown格式的报告字符串
        """
        md = f"""# 房都督 · 个人综合决策报告

**报告编号**: {report.report_id}  
**生成时间**: {report.generated_at}  
**解读人**: {report.interpreter}

---

## 一、您的核心信息

"""
        # 用户信息
        user_info = report.user_info
        if user_info.get("birth_year"):
            md += f"- **出生**: {user_info.get('birth_year')}年"
            if user_info.get("birth_month"):
                md += f"{user_info.get('birth_month')}月{user_info.get('birth_day')}日"
            md += f"（属{user_info.get('zodiac', '未知')}，{user_info.get('age', '')}周岁）\n"
        
        if user_info.get("profession"):
            md += f"- **职业**: {user_info.get('profession')}\n"
        if user_info.get("city"):
            md += f"- **当前城市**: {user_info.get('city')}\n"
        if user_info.get("status"):
            md += f"- **状态**: {user_info.get('status')}\n"
        if user_info.get("question"):
            md += f"- **诉求**: {user_info.get('question')}\n"
        
        md += "\n---\n\n## 二、六维框架深度分析\n\n"
        
        # 六维分析
        dims = report.six_dimensions
        dimension_names = {
            "pattern": ("格局定基调", "您的天赋赛道"),
            "wealth": ("财运通道", "正偏财有别"),
            "marriage": ("姻缘逻辑", "你是谁，才遇到谁"),
            "career": ("事业路径", "不是选行业，是选节点"),
            "social": ("人际过滤", "滋养与消耗"),
            "execution": ("执行力与心态", "决定命盘兑现率")
        }
        
        for dim_key, (dim_title, dim_subtitle) in dimension_names.items():
            dim_data = dims.get(dim_key, {})
            if dim_data:
                md += f"### 维度{list(dimension_names.keys()).index(dim_key) + 1}：{dim_title}——{dim_subtitle}\n\n"
                
                if dim_data.get("summary"):
                    md += f"**{dim_data['summary']}**\n\n"
                if dim_data.get("trait"):
                    md += f"您的命盘里带{dim_data.get('trait', '')}。\n\n"
                if dim_data.get("issue"):
                    md += f"**问题**: {dim_data['issue']}\n\n"
                if dim_data.get("advice"):
                    md += f"**建议**: {dim_data['advice']}\n\n"
                if dim_data.get("choice"):
                    md += f"**选择**: {dim_data['choice']}\n\n"
                
                md += "\n"
        
        md += "---\n\n## 三、平台给您的最终建议\n\n"
        
        # 建议
        for i, rec in enumerate(report.recommendations, 1):
            md += f"### {i}. {rec.get('title', '建议' + str(i))}\n\n"
            if rec.get("content"):
                md += f"{rec['content']}\n\n"
            if rec.get("timeline"):
                md += f"**时间线**: {rec['timeline']}\n\n"
            if rec.get("reason"):
                md += f"**理由**: {rec['reason']}\n\n"
        
        md += "---\n\n## 四、可执行步骤\n\n"
        
        # 行动步骤
        for step in report.action_steps:
            step_num = step.get("step", 1)
            md += f"### 步骤{step_num}: {step.get('title', step.get('action', ''))}\n\n"
            if step.get("action") and step.get("title"):
                md += f"{step['action']}\n\n"
            if step.get("timeline"):
                md += f"**时间**: {step['timeline']}\n\n"
        
        # 案例参考
        if report.case_references:
            md += "---\n\n## 五、案例参考\n\n"
            md += "以下是案例库中与您情况相似的真实案例（已脱敏）：\n\n"
            for i, case in enumerate(report.case_references, 1):
                md += f"### 案例{i}: {case.get('title', '相似案例')}\n\n"
                if case.get("situation"):
                    md += f"**情况**: {case['situation']}\n\n"
                if case.get("decision"):
                    md += f"**决策**: {case['decision']}\n\n"
                if case.get("outcome"):
                    md += f"**结果**: {case['outcome']}\n\n"
        
        md += f"""---

## 六、写在最后

您的案例已经存入平台案例库（编号4000+），以后有人遇到类似的岔路口，您的脚印会成为他们的路标。

**周瑜**: 您还年轻，路还长。每一步都算数。

**陆逊**: 等您达成目标那天，记得来敲我们。到时候，这份报告会多一条注脚——后记。

---

## 免责声明

{report.disclaimer}

---

**房都督**: 我们不是来替您选路的，是来帮您看清路的。路在脚下，您随时可以走。
"""
        
        return md
    
    def format_report_json(self, report: PersonalDecisionReport) -> str:
        """将报告格式化为JSON"""
        return json.dumps({
            "report_id": report.report_id,
            "generated_at": report.generated_at,
            "interpreter": report.interpreter,
            "user_info": report.user_info,
            "six_dimensions": report.six_dimensions,
            "recommendations": report.recommendations,
            "action_steps": report.action_steps,
            "case_references": report.case_references,
            "disclaimer": report.disclaimer
        }, ensure_ascii=False, indent=2)

# 全局报告生成器实例
report_generator = ReportGenerator()
