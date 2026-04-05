"""
命盘案例库API路由
提供案例录入、检索、分析和报告生成功能
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import random

from ..models.mingpan_case import (
    CaseFull, CaseCreateRequest, CaseSearchRequest, CaseStatistics,
    PatternType, WealthType, MarriageLevel, CareerStage, RelationType, ExecutionLevel,
    SAMPLE_CASES, CASE_TABLE_SCHEMA
)

router = APIRouter(prefix="/api/mingpan", tags=["mingpan"])


class LaohaiReportRequest(BaseModel):
    """老骇风格报告请求"""
    case_id: str
    report_type: str = "full"


class LaohaiReportResponse(BaseModel):
    """老骇风格报告响应"""
    case_id: str
    report_title: str
    report_content: str
    dimension_summary: Dict[str, str]
    key_insights: List[str]
    suggestions: List[str]
    laohai_signature: str


_in_memory_cases: Dict[str, Dict[str, Any]] = {}


def _init_sample_cases():
    """初始化示例案例"""
    for case in SAMPLE_CASES:
        _in_memory_cases[case["case_id"]] = case


_init_sample_cases()


@router.post("/cases", response_model=CaseFull)
async def create_case(request: CaseCreateRequest):
    """
    创建新的命盘案例
    
    Args:
        request: 案例创建请求
        
    Returns:
        CaseFull: 完整案例信息
    """
    import uuid
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    
    case_data = request.dict()
    case_data["case_id"] = case_id
    case_data["created_at"] = datetime.now().isoformat()
    case_data["updated_at"] = datetime.now().isoformat()
    
    if case_data.get("dimension_analysis"):
        da = case_data["dimension_analysis"]
        case_data["dimension_1_pattern"] = da.get("dimension_1_pattern", {})
        case_data["dimension_2_wealth"] = da.get("dimension_2_wealth", {})
        case_data["dimension_3_marriage"] = da.get("dimension_3_marriage", {})
        case_data["dimension_4_career"] = da.get("dimension_4_career", {})
        case_data["dimension_5_relations"] = da.get("dimension_5_relations", {})
        case_data["dimension_6_execution"] = da.get("dimension_6_execution", {})
    
    _in_memory_cases[case_id] = case_data
    
    return CaseFull(**case_data)


@router.get("/cases/{case_id}", response_model=CaseFull)
async def get_case(case_id: str):
    """
    获取案例详情
    
    Args:
        case_id: 案例ID
        
    Returns:
        CaseFull: 完整案例信息
    """
    if case_id not in _in_memory_cases:
        raise HTTPException(status_code=404, detail="案例不存在")
    
    case_data = _in_memory_cases[case_id]
    return CaseFull(**case_data)


@router.get("/cases", response_model=List[CaseFull])
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    pattern_type: Optional[PatternType] = None,
    wealth_type: Optional[WealthType] = None,
    gender: Optional[str] = None,
    outcome_status: Optional[str] = None
):
    """
    列出案例列表，支持筛选
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        pattern_type: 格局类型筛选
        wealth_type: 财运类型筛选
        gender: 性别筛选
        outcome_status: 结果状态筛选
        
    Returns:
        List[CaseFull]: 案例列表
    """
    cases = list(_in_memory_cases.values())
    
    if pattern_type:
        cases = [c for c in cases if c.get("dimension_1_pattern", {}).get("type") == pattern_type.value]
    
    if wealth_type:
        cases = [c for c in cases if c.get("dimension_2_wealth", {}).get("type") == wealth_type.value]
    
    if gender:
        cases = [c for c in cases if c.get("gender") == gender]
    
    if outcome_status:
        cases = [c for c in cases if c.get("outcome_status") == outcome_status]
    
    return [CaseFull(**c) for c in cases[skip:skip+limit]]


@router.post("/search", response_model=List[CaseFull])
async def search_cases(request: CaseSearchRequest):
    """
    高级搜索案例
    
    Args:
        request: 搜索请求
        
    Returns:
        List[CaseFull]: 匹配的案例列表
    """
    cases = list(_in_memory_cases.values())
    
    if request.pattern_type:
        cases = [c for c in cases if c.get("dimension_1_pattern", {}).get("type") == request.pattern_type.value]
    
    if request.wealth_type:
        cases = [c for c in cases if c.get("dimension_2_wealth", {}).get("type") == request.wealth_type.value]
    
    if request.marriage_level:
        cases = [c for c in cases if c.get("dimension_3_marriage", {}).get("level") == request.marriage_level.value]
    
    if request.career_stage:
        cases = [c for c in cases if c.get("dimension_4_career", {}).get("stage") == request.career_stage.value]
    
    if request.relation_type:
        cases = [c for c in cases if c.get("dimension_5_relations", {}).get("family_type") == request.relation_type.value]
    
    if request.execution_level:
        cases = [c for c in cases if c.get("dimension_6_execution", {}).get("level") == request.execution_level.value]
    
    if request.gender:
        cases = [c for c in cases if c.get("gender") == request.gender]
    
    if request.keyword:
        keyword = request.keyword.lower()
        cases = [c for c in cases if 
                 keyword in c.get("background", "").lower() or
                 keyword in c.get("laohai_comment", "").lower() or
                 any(keyword in tag.lower() for tag in c.get("tags", []))]
    
    if request.tags:
        cases = [c for c in cases if any(tag in c.get("tags", []) for tag in request.tags)]
    
    return [CaseFull(**c) for c in cases]


@router.get("/statistics", response_model=CaseStatistics)
async def get_statistics():
    """
    获取案例统计数据
    
    Returns:
        CaseStatistics: 统计数据
    """
    cases = list(_in_memory_cases.values())
    
    pattern_dist = {}
    wealth_dist = {}
    execution_success = {}
    
    for case in cases:
        pattern = case.get("dimension_1_pattern", {}).get("type", "未知")
        pattern_dist[pattern] = pattern_dist.get(pattern, 0) + 1
        
        wealth = case.get("dimension_2_wealth", {}).get("type", "未知")
        wealth_dist[wealth] = wealth_dist.get(wealth, 0) + 1
        
        exec_level = case.get("dimension_6_execution", {}).get("level", "未知")
        if exec_level not in execution_success:
            execution_success[exec_level] = {"total": 0, "success": 0}
        execution_success[exec_level]["total"] += 1
        if case.get("outcome_status") == "已破局":
            execution_success[exec_level]["success"] += 1
    
    exec_rates = {k: round(v["success"] / v["total"] * 100, 1) if v["total"] > 0 else 0 
                  for k, v in execution_success.items()}
    
    blockages = {}
    for case in cases:
        blockage = case.get("dimension_1_pattern", {}).get("blockage")
        if blockage:
            blockages[blockage] = blockages.get(blockage, 0) + 1
    
    common_blockages = [{"blockage": k, "count": v} for k, v in sorted(blockages.items(), key=lambda x: -x[1])[:5]]
    
    breakthroughs = []
    for case in cases:
        if case.get("outcome_status") == "已破局":
            breakthroughs.append({
                "case_id": case.get("case_id"),
                "pattern_type": case.get("dimension_1_pattern", {}).get("type"),
                "turning_point": case.get("outcome_turning_point"),
                "rating": case.get("outcome_rating", 0)
            })
    
    breakthroughs.sort(key=lambda x: -x["rating"])
    
    return CaseStatistics(
        total_cases=len(cases),
        pattern_distribution=pattern_dist,
        wealth_distribution=wealth_dist,
        execution_success_rate=exec_rates,
        common_blockages=common_blockages,
        breakthrough_patterns=breakthroughs[:10]
    )


@router.post("/report/laohai", response_model=LaohaiReportResponse)
async def generate_laohai_report(request: LaohaiReportRequest):
    """
    生成老骇风格的分析报告
    
    Args:
        request: 报告生成请求
        
    Returns:
        LaohaiReportResponse: 老骇风格报告
    """
    if request.case_id not in _in_memory_cases:
        raise HTTPException(status_code=404, detail="案例不存在")
    
    case = _in_memory_cases[request.case_id]
    
    report = _generate_laohai_style_report(case)
    
    return report


def _generate_laohai_style_report(case: Dict[str, Any]) -> LaohaiReportResponse:
    """生成老骇风格报告"""
    
    name = case.get("anonymized_name", "某人")
    pattern = case.get("dimension_1_pattern", {})
    wealth = case.get("dimension_2_wealth", {})
    marriage = case.get("dimension_3_marriage", {})
    career = case.get("dimension_4_career", {})
    relations = case.get("dimension_5_relations", {})
    execution = case.get("dimension_6_execution", {})
    outcome = case.get("outcome_status", "未知")
    
    report_title = f"命盘案例深度分析：{name}"
    
    intro = f"这案例我看了好几遍。{name}，{case.get('gender', '')}，{case.get('birth_year', '')}年生，{case.get('birth_place', '')}人。"
    intro += f"现居{case.get('current_location', '')}。\n\n"
    intro += f"背景是这样的：{case.get('background', '')}\n\n"
    
    dim1_analysis = f"【格局分析】\n这人是{pattern.get('type', '未知')}。"
    if pattern.get("description"):
        dim1_analysis += f"{pattern.get('description')}。"
    if pattern.get("blockage"):
        dim1_analysis += f"卡点在于：{pattern.get('blockage')}。"
    if pattern.get("suggestion"):
        dim1_analysis += f"我的建议是：{pattern.get('suggestion')}。"
    
    dim2_analysis = f"\n\n【财运通道】\n{wealth.get('type', '未知')}。"
    if wealth.get("description"):
        dim2_analysis += f"{wealth.get('description')}。"
    if wealth.get("warning"):
        dim2_analysis += f"⚠️ {wealth.get('warning')}。"
    
    dim3_analysis = f"\n\n【姻缘逻辑】\n段位：{marriage.get('level', '未知')}。"
    if marriage.get("gap_analysis"):
        dim3_analysis += f"{marriage.get('gap_analysis')}。"
    if marriage.get("suggestion"):
        dim3_analysis += f"建议：{marriage.get('suggestion')}。"
    
    dim4_analysis = f"\n\n【事业路径】\n当前阶段：{career.get('stage', '未知')}。"
    if career.get("node_analysis"):
        dim4_analysis += f"{career.get('node_analysis')}。"
    if career.get("next_step"):
        dim4_analysis += f"下一步：{career.get('next_step')}。"
    
    dim5_analysis = f"\n\n【人际过滤】\n家庭关系：{relations.get('family_type', '未知')}。"
    if relations.get("protection_strategy"):
        dim5_analysis += f"应对策略：{relations.get('protection_strategy')}。"
    
    dim6_analysis = f"\n\n【执行力心态】\n执行力：{execution.get('level', '未知')}。"
    if execution.get("blockage"):
        dim6_analysis += f"卡点：{execution.get('blockage')}。"
    dim6_analysis += f"兑现率：{execution.get('realization_rate', 0) * 100:.0f}%。"
    
    outcome_analysis = f"\n\n【结果分析】\n当前状态：{outcome}。"
    if case.get("outcome_turning_point"):
        outcome_analysis += f"关键转折点：{case.get('outcome_turning_point')}。"
    
    laohai_comment = case.get("laohai_comment", "")
    if laohai_comment:
        outcome_analysis += f"\n\n【老骇点评】\n{laohai_comment}"
    
    conclusion = "\n\n【总结】\n命盘是地图，你是司机。这案例的关键在于——"
    if pattern.get("type"):
        conclusion += f"认清自己是{pattern.get('type')}，"
    if outcome == "已破局":
        conclusion += "然后动起来了。很多人命盘不差，就是不动。"
    elif outcome == "困局中":
        conclusion += "但卡在了某个节点。需要找到突破口。"
    else:
        conclusion += "正在破局路上，继续观察。"
    
    report_content = intro + dim1_analysis + dim2_analysis + dim3_analysis + dim4_analysis + dim5_analysis + dim6_analysis + outcome_analysis + conclusion
    
    dimension_summary = {
        "格局": f"{pattern.get('type', '未知')} - {pattern.get('description', '')}",
        "财运": f"{wealth.get('type', '未知')} - {wealth.get('description', '')}",
        "姻缘": f"{marriage.get('level', '未知')}段位",
        "事业": f"{career.get('stage', '未知')}",
        "人际": f"{relations.get('family_type', '未知')}",
        "执行力": f"{execution.get('level', '未知')} (兑现率{execution.get('realization_rate', 0)*100:.0f}%)"
    }
    
    key_insights = []
    if pattern.get("blockage"):
        key_insights.append(f"卡点：{pattern.get('blockage')}")
    if wealth.get("warning"):
        key_insights.append(f"警示：{wealth.get('warning')}")
    if case.get("outcome_turning_point"):
        key_insights.append(f"转折点：{case.get('outcome_turning_point')}")
    
    lessons = case.get("outcome_lessons", [])
    key_insights.extend(lessons)
    
    suggestions = []
    if pattern.get("suggestion"):
        suggestions.append(pattern.get("suggestion"))
    if marriage.get("suggestion"):
        suggestions.append(marriage.get("suggestion"))
    if career.get("next_step"):
        suggestions.append(career.get("next_step"))
    if relations.get("protection_strategy"):
        suggestions.append(f"人际策略：{relations.get('protection_strategy')}")
    
    return LaohaiReportResponse(
        case_id=case.get("case_id"),
        report_title=report_title,
        report_content=report_content,
        dimension_summary=dimension_summary,
        key_insights=key_insights,
        suggestions=suggestions,
        laohai_signature="老骇\n2026.03.23"
    )


@router.get("/report/batch")
async def generate_batch_report(
    pattern_type: Optional[PatternType] = None,
    min_rating: int = Query(0, ge=0, le=100)
):
    """
    生成批量分析报告
    
    Args:
        pattern_type: 格局类型筛选
        min_rating: 最低评分筛选
        
    Returns:
        Dict: 批量报告
    """
    cases = list(_in_memory_cases.values())
    
    if pattern_type:
        cases = [c for c in cases if c.get("dimension_1_pattern", {}).get("type") == pattern_type.value]
    
    cases = [c for c in cases if c.get("outcome_rating", 0) >= min_rating]
    
    cases.sort(key=lambda x: -x.get("outcome_rating", 0))
    
    report = {
        "title": "命盘案例库批量分析报告",
        "generated_at": datetime.now().isoformat(),
        "total_cases": len(cases),
        "summary": {
            "avg_rating": sum(c.get("outcome_rating", 0) for c in cases) / len(cases) if cases else 0,
            "success_rate": len([c for c in cases if c.get("outcome_status") == "已破局"]) / len(cases) * 100 if cases else 0
        },
        "cases": [
            {
                "case_id": c.get("case_id"),
                "name": c.get("anonymized_name"),
                "pattern": c.get("dimension_1_pattern", {}).get("type"),
                "outcome": c.get("outcome_status"),
                "rating": c.get("outcome_rating"),
                "key_lesson": c.get("outcome_lessons", [""])[0] if c.get("outcome_lessons") else ""
            }
            for c in cases[:20]
        ],
        "laohai_summary": _generate_batch_laohai_summary(cases)
    }
    
    return report


def _generate_batch_laohai_summary(cases: List[Dict]) -> str:
    """生成批量老骇风格总结"""
    if not cases:
        return "暂无数据。"
    
    success_cases = [c for c in cases if c.get("outcome_status") == "已破局"]
    stuck_cases = [c for c in cases if c.get("outcome_status") == "困局中"]
    
    summary = f"这批案例共{len(cases)}个，其中{len(success_cases)}个已破局，{len(stuck_cases)}个还在困局中。\n\n"
    
    if success_cases:
        summary += "破局的案例有个共同点——"
        patterns = [c.get("dimension_1_pattern", {}).get("type") for c in success_cases if c.get("dimension_1_pattern", {}).get("type")]
        if patterns:
            from collections import Counter
            pattern_counts = Counter(patterns)
            most_common = pattern_counts.most_common(1)[0][0]
            summary += f"{most_common}的人占比较高。"
        summary += "关键不是命盘有多好，而是他们动起来了。\n\n"
    
    if stuck_cases:
        summary += "困局的案例，问题多半出在——"
        blockages = [c.get("dimension_1_pattern", {}).get("blockage") for c in stuck_cases if c.get("dimension_1_pattern", {}).get("blockage")]
        if blockages:
            summary += f"{blockages[0]}。"
        summary += "认清卡点，才能找到出口。\n\n"
    
    summary += "命盘是地图，你是司机。地图再好，也得有人走。"
    
    return summary


@router.get("/tags")
async def get_all_tags():
    """获取所有标签"""
    all_tags = set()
    for case in _in_memory_cases.values():
        for tag in case.get("tags", []):
            all_tags.add(tag)
    return {"tags": sorted(list(all_tags))}


@router.get("/count")
async def get_case_count():
    """获取案例总数"""
    return {"total": len(_in_memory_cases)}
