"""
演示模式API
Demo Mode API

为前端演示体验提供预设数据
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import time
import asyncio

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoRequest(BaseModel):
    message: str
    demo: bool = True
    step: Optional[int] = None


class DemoResponse(BaseModel):
    reply: str
    task_id: str
    agent_status: Dict[str, str]
    step: int
    is_complete: bool
    report_data: Optional[Dict[str, Any]] = None


DEMO_SCENARIO = {
    "user_query": "我想在深圳南山区买一套100平米左右的学区房，预算1000万，帮我分析一下。",
    "steps": [
        {
            "agent": "zhongshu",
            "agent_name": "中书省",
            "message": "周瑜：收到您的需求。让我来分析一下——深圳南山区，学区房，100平米，预算1000万。这是一个典型的学区房置业决策，我将协调各部为您进行全面分析。",
            "delay": 1.5,
        },
        {
            "agent": "bingbu",
            "agent_name": "兵部",
            "message": "【兵部】正在采集南山区学区房数据...\n✓ 已获取南山区12个学区信息\n✓ 已采集近3个月成交数据\n✓ 已获取学区划分及对口学校信息",
            "delay": 2.0,
        },
        {
            "agent": "gongbu",
            "agent_name": "工部",
            "message": "【工部】正在进行估值分析...\n\n📊 南山区学区房市场分析：\n• 均价区间：9-15万/㎡\n• 100㎡预算匹配度：中等\n• 推荐学区：南二外、南山实验、育才\n\n💰 估值结果：\n• 南二外学区：约1100-1300万\n• 南山实验学区：约950-1150万\n• 育才学区：约850-1000万",
            "delay": 3.0,
        },
        {
            "agent": "xingbu",
            "agent_name": "刑部",
            "message": "【刑部】风险评估报告：\n\n⚠️ 注意事项：\n• 深圳限购政策：需深圳户口或连续5年社保\n• 学区政策变动风险：中等\n• 价格波动风险：需关注政策调控\n\n✅ 风险等级：可控",
            "delay": 2.0,
        },
        {
            "agent": "menshang",
            "agent_name": "门下省",
            "message": "【门下省】审核通过\n\n经核查，以上分析数据来源可靠，估值方法科学，风险提示充分。建议重点关注南山实验学区的房源，性价比较高。",
            "delay": 1.5,
        },
        {
            "agent": "libu",
            "agent_name": "礼部",
            "message": "周瑜：综合各部分析，我为您整理了以下建议：\n\n🏠 推荐方案：\n1. 首选南山实验学区，预算匹配度高\n2. 关注育才学区作为备选\n3. 建议实地考察3-5套房源后再做决定\n\n📋 下一步行动：\n• 准备购房资格证明\n• 关注近期新上房源\n• 联系中介实地看房\n\n如需更详细的分析报告，我可以为您生成专属报告。",
            "delay": 2.5,
        },
    ],
}

REPORT_DATA = {
    "title": "深圳南山区学区房分析报告",
    "summary": "基于您的需求和预算，我们为您分析了南山区的学区房市场",
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "user_requirement": {
        "location": "深圳南山区",
        "area": "100平米",
        "budget": "1000万",
        "type": "学区房"
    },
    "recommendations": [
        {
            "area": "南山实验学区",
            "price_range": "9.5-11.5万/㎡",
            "total_price": "950-1150万",
            "match_score": 95,
            "reason": "预算匹配度高，学区优质",
            "schools": ["南山实验学校", "南山实验中学"],
            "nearby": ["海岸城", "深圳湾公园", "人才公园"]
        },
        {
            "area": "育才学区",
            "price_range": "8.5-10万/㎡",
            "total_price": "850-1000万",
            "match_score": 90,
            "reason": "性价比高，学区稳定",
            "schools": ["育才一小", "育才二中"],
            "nearby": ["蛇口海上世界", "南山文体中心"]
        },
        {
            "area": "南二外学区",
            "price_range": "11-13万/㎡",
            "total_price": "1100-1300万",
            "match_score": 75,
            "reason": "顶级学区，略超预算",
            "schools": ["南山第二外国语学校"],
            "nearby": ["科技园", "深圳大学"]
        }
    ],
    "price_trend": [
        {"month": "7月", "price": 10.2, "volume": 1250},
        {"month": "8月", "price": 10.5, "volume": 1180},
        {"month": "9月", "price": 10.3, "volume": 1320},
        {"month": "10月", "price": 10.8, "volume": 1450},
        {"month": "11月", "price": 10.6, "volume": 1380},
        {"month": "12月", "price": 10.9, "volume": 1520},
    ],
    "risk_analysis": {
        "policy_risk": {
            "level": "中",
            "description": "深圳限购政策持续，需关注政策变动"
        },
        "price_risk": {
            "level": "中低",
            "description": "南山区房价相对稳定，波动幅度可控"
        },
        "school_risk": {
            "level": "低",
            "description": "学区划分相对稳定，近期无重大调整"
        }
    },
    "action_items": [
        "准备购房资格证明（户口本/社保缴纳证明）",
        "关注南山实验学区近期新上房源",
        "预约中介实地看房（建议3-5套）",
        "了解贷款政策，评估首付能力",
        "关注学区政策最新动态"
    ]
}


@router.post("/chat", response_model=DemoResponse)
async def demo_chat(request: DemoRequest):
    """
    演示模式聊天接口
    
    返回预设的演示数据，模拟真实的智能体交互流程
    """
    if not request.demo:
        raise HTTPException(status_code=400, detail="This endpoint is for demo mode only")
    
    step = request.step if request.step is not None else 0
    
    if step >= len(DEMO_SCENARIO["steps"]):
        return DemoResponse(
            reply="演示已完成",
            task_id="demo_task_001",
            agent_status={agent["agent"]: "completed" for agent in DEMO_SCENARIO["steps"]},
            step=step,
            is_complete=True,
            report_data=REPORT_DATA
        )
    
    current_step = DEMO_SCENARIO["steps"][step]
    
    agent_status = {}
    for i, agent_step in enumerate(DEMO_SCENARIO["steps"]):
        if i < step:
            agent_status[agent_step["agent"]] = "completed"
        elif i == step:
            agent_status[agent_step["agent"]] = "working"
        else:
            agent_status[agent_step["agent"]] = "idle"
    
    await asyncio.sleep(current_step["delay"] * 0.1)
    
    return DemoResponse(
        reply=current_step["message"],
        task_id="demo_task_001",
        agent_status=agent_status,
        step=step + 1,
        is_complete=(step + 1 >= len(DEMO_SCENARIO["steps"])),
        report_data=REPORT_DATA if (step + 1 >= len(DEMO_SCENARIO["steps"])) else None
    )


@router.get("/scenario")
async def get_demo_scenario():
    """获取演示场景配置"""
    return {
        "user_query": DEMO_SCENARIO["user_query"],
        "total_steps": len(DEMO_SCENARIO["steps"]),
        "agents": list(set(step["agent"] for step in DEMO_SCENARIO["steps"])),
        "estimated_duration": sum(step["delay"] for step in DEMO_SCENARIO["steps"])
    }


@router.get("/report")
async def get_demo_report():
    """获取演示报告数据"""
    return REPORT_DATA


@router.post("/start")
async def start_demo():
    """开始演示会话"""
    return {
        "session_id": f"demo_session_{int(time.time())}",
        "user_query": DEMO_SCENARIO["user_query"],
        "initial_step": 0,
        "message": "演示会话已创建，请发送用户消息开始"
    }
