"""
报告生成API路由
提供报告生成、查询、导出等功能
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..services.report_template import report_generator, PersonalDecisionReport
from ..services.case_library import case_library
from ..auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["报告"])

class UserInfoInput(BaseModel):
    """用户信息输入"""
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    birth_hour: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    profession: Optional[str] = None
    status: Optional[str] = None
    question: Optional[str] = None

class AnalysisInput(BaseModel):
    """六维分析输入"""
    pattern: Optional[Dict[str, Any]] = None
    wealth: Optional[Dict[str, Any]] = None
    marriage: Optional[Dict[str, Any]] = None
    career: Optional[Dict[str, Any]] = None
    social: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None

class RecommendationInput(BaseModel):
    """建议输入"""
    title: str
    content: str
    timeline: Optional[str] = None
    reason: Optional[str] = None

class ActionStepInput(BaseModel):
    """行动步骤输入"""
    step: int
    title: Optional[str] = None
    action: str
    timeline: Optional[str] = None

class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    report_type: str = Field(..., description="报告类型: emotion/career/property/combined")
    user_info: UserInfoInput
    analysis: AnalysisInput
    recommendations: List[RecommendationInput]
    action_steps: List[ActionStepInput]
    include_cases: bool = Field(True, description="是否包含相似案例参考")

class GenerateReportResponse(BaseModel):
    """生成报告响应"""
    report_id: str
    generated_at: str
    markdown: str
    json_data: Dict[str, Any]

@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    生成个人综合决策报告
    
    根据用户信息和六维分析生成标准化报告
    """
    try:
        user_info_dict = request.user_info.model_dump(exclude_none=True)
        analysis_dict = request.analysis.model_dump(exclude_none=True)
        recommendations_list = [r.model_dump() for r in request.recommendations]
        action_steps_list = [s.model_dump() for s in request.action_steps]
        
        case_references = []
        if request.include_cases:
            zodiac = user_info_dict.get("zodiac", "")
            similar_cases = case_library.search_similar_cases(
                zodiac=zodiac,
                case_type=None,
                question_category=user_info_dict.get("question_category"),
                limit=3
            )
            for case in similar_cases:
                case_references.append({
                    "title": f"案例{case.id}",
                    "situation": case.question[:100] + "..." if len(case.question) > 100 else case.question,
                    "decision": case.final_decision,
                    "outcome": case.outcome
                })
        
        report = report_generator.generate_report(
            report_type=request.report_type,
            user_info=user_info_dict,
            analysis=analysis_dict,
            recommendations=recommendations_list,
            action_steps=action_steps_list,
            case_references=case_references
        )
        
        markdown_output = report_generator.format_report_markdown(report)
        json_output = report_generator.format_report_json(report)
        
        return GenerateReportResponse(
            report_id=report.report_id,
            generated_at=report.generated_at,
            markdown=markdown_output,
            json_data=json.loads(json_output)
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取报告详情
    
    根据报告ID获取已生成的报告
    """
    pass

@router.get("/{report_id}/export/pdf")
async def export_report_pdf(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    导出报告为PDF
    
    将报告导出为PDF格式下载
    """
    pass

@router.get("/{report_id}/export/docx")
async def export_report_docx(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    导出报告为Word文档
    
    将报告导出为Word格式下载
    """
    pass

@router.get("/templates/list")
async def list_report_templates():
    """
    获取报告模板列表
    
    返回所有可用的报告模板
    """
    return {
        "templates": [
            {
                "type": "emotion",
                "name": "情感决策报告",
                "description": "针对感情问题的深度分析报告"
            },
            {
                "type": "career",
                "name": "事业决策报告",
                "description": "针对职业发展的深度分析报告"
            },
            {
                "type": "property",
                "name": "房产决策报告",
                "description": "针对房产购买的深度分析报告"
            },
            {
                "type": "combined",
                "name": "个人综合决策报告",
                "description": "综合命盘与房产的全面分析报告"
            }
        ]
    }

@router.post("/quick-analysis")
async def quick_analysis(
    user_input: str,
    current_user: dict = Depends(get_current_user)
):
    """
    快速分析入口
    
    根据用户输入快速生成初步分析
    """
    from ..services.six_dimension_dialogue import dialogue_system
    
    response = dialogue_system.generate_response(user_input)
    
    return {
        "input": user_input,
        "response": response["response"],
        "style": response["style"],
        "follow_up": response.get("follow_up"),
        "related_dimensions": response.get("related_dimensions", []),
        "category": response.get("category")
    }
