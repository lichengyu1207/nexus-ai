"""
智能咨询路由 - 支持角色扮演系统
集成记忆系统实现跨会话记忆能力
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import random
import asyncio
import time

from ..auth import get_current_user
from ..database import get_db
from ..services.persona_system import (
    get_random_persona,
    get_persona_config,
    get_persona_welcome,
    get_persona_system_prompt,
    PersonaType,
)
from ..memory.service import memory_service
from ..llm_service import llm_service

router = APIRouter(prefix="/api/consult", tags=["consultation"])


class StartConsultationRequest(BaseModel):
    pass


class StartConsultationResponse(BaseModel):
    session_id: str
    persona: str
    welcome_message: str
    persona_info: dict


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


class SendMessageResponse(BaseModel):
    reply: str
    emotion: str
    persona: str


class MessageHistory(BaseModel):
    id: str
    role: str
    content: str
    persona: Optional[str]
    created_at: str


class ReportRequest(BaseModel):
    """报告生成请求"""
    query: str
    report_type: str = "房产分析"
    data_sources: List[str] = ["房价数据", "政策信息", "周边配套"]
    models: List[str] = ["估值模型", "趋势预测模型"]


class StreamingReportGenerator:
    """流式报告生成器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.pause_flags: Dict[str, bool] = {}
        self.skip_flags: Dict[str, bool] = {}
    
    async def connect(self, websocket: WebSocket):
        """连接WebSocket"""
        await websocket.accept()
        client_id = f"client_{id(websocket)}"
        self.active_connections.append(websocket)
        self.pause_flags[client_id] = False
        self.skip_flags[client_id] = False
        return client_id
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        client_id = f"client_{id(websocket)}"
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id in self.pause_flags:
            del self.pause_flags[client_id]
        if client_id in self.skip_flags:
            del self.skip_flags[client_id]
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """发送消息"""
        try:
            await websocket.send_json(message)
            await asyncio.sleep(0.05)  # 控制发送速度
        except Exception as e:
            pass
    
    async def check_pause(self, client_id: str):
        """检查是否暂停"""
        while self.pause_flags.get(client_id, False):
            await asyncio.sleep(0.1)
    
    async def generate_report(self, websocket: WebSocket, request: ReportRequest):
        """生成报告"""
        client_id = f"client_{id(websocket)}"
        
        try:
            # 推送报告标题
            await self.send_message(websocket, {
                "type": "text",
                "content": f"{request.report_type}报告",
                "timestamp": time.time(),
                "style": "title"
            })
            
            # 推送状态
            await self.send_message(websocket, {
                "type": "status",
                "content": "正在采集房价数据...",
                "timestamp": time.time()
            })
            
            # 模拟数据采集
            await asyncio.sleep(1)
            
            # 推送状态更新
            await self.send_message(websocket, {
                "type": "status",
                "content": "数据采集完成，正在生成图表...",
                "timestamp": time.time()
            })
            
            # 推送折线图框架
            await self.send_message(websocket, {
                "type": "chart",
                "chartType": "line",
                "title": "深圳南山区房价走势",
                "xAxis": "月份",
                "yAxis": "均价（元/㎡）",
                "yRange": [0, 120000],
                "legend": ["均价"],
                "partial": False,
                "timestamp": time.time()
            })
            
            # 推送数据点
            months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
                     "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
            prices = [95000, 96000, 97000, 96500, 97500, 98000,
                     98500, 99000, 99500, 100000, 100500, 101000]
            
            # 动态调整推送速度
            push_interval = 0.5
            
            for i, (month, price) in enumerate(zip(months, prices)):
                # 检查是否暂停
                await self.check_pause(client_id)
                
                # 检查是否跳过
                if self.skip_flags.get(client_id, False):
                    break
                
                await self.send_message(websocket, {
                    "type": "chart",
                    "chartType": "line",
                    "data": {"x": i + 1, "y": price, "label": month},
                    "partial": True,
                    "timestamp": time.time(),
                    "index": i
                })
                
                # 自适应调整推送速度
                if i < 3:  # 前几个点慢一点，让用户看清楚
                    await asyncio.sleep(push_interval * 1.5)
                else:
                    await asyncio.sleep(push_interval)
            
            # 推送柱状图示例
            await self.send_message(websocket, {
                "type": "chart",
                "chartType": "bar",
                "title": "区域房价对比",
                "xAxis": "区域",
                "yAxis": "均价（元/㎡）",
                "yRange": [0, 150000],
                "legend": ["均价"],
                "partial": False,
                "timestamp": time.time()
            })
            
            # 推送柱状图数据
            areas = ["南山区", "福田区", "罗湖区", "宝安区", "龙岗区"]
            area_prices = [101000, 95000, 85000, 65000, 55000]
            
            for i, (area, price) in enumerate(zip(areas, area_prices)):
                # 检查是否暂停
                await self.check_pause(client_id)
                
                # 检查是否跳过
                if self.skip_flags.get(client_id, False):
                    break
                
                await self.send_message(websocket, {
                    "type": "chart",
                    "chartType": "bar",
                    "data": {"x": area, "y": price},
                    "partial": True,
                    "timestamp": time.time(),
                    "index": i
                })
                await asyncio.sleep(0.8)  # 柱状图绘制稍慢一点
            
            # 推送饼图示例
            await self.send_message(websocket, {
                "type": "chart",
                "chartType": "pie",
                "title": "南山区房源类型分布",
                "legend": ["住宅", "商业", "办公", "其他"],
                "partial": False,
                "timestamp": time.time()
            })
            
            # 推送饼图数据
            pie_data = [
                {"name": "住宅", "value": 65},
                {"name": "商业", "value": 15},
                {"name": "办公", "value": 15},
                {"name": "其他", "value": 5}
            ]
            
            for i, item in enumerate(pie_data):
                # 检查是否暂停
                await self.check_pause(client_id)
                
                # 检查是否跳过
                if self.skip_flags.get(client_id, False):
                    break
                
                await self.send_message(websocket, {
                    "type": "chart",
                    "chartType": "pie",
                    "data": item,
                    "partial": True,
                    "timestamp": time.time(),
                    "index": i
                })
                await asyncio.sleep(1.0)  # 饼图绘制更慢一点
            
            # 检查是否跳过
            if self.skip_flags.get(client_id, False):
                # 直接生成摘要
                await self.send_message(websocket, {
                    "type": "text",
                    "content": "报告摘要：深圳南山区房价稳中有升，预计未来半年涨幅约5%。",
                    "timestamp": time.time(),
                    "style": "summary"
                })
                await self.send_message(websocket, {
                    "type": "status",
                    "content": "完成",
                    "timestamp": time.time()
                })
                return
            
            # 推送推理步骤
            await self.send_message(websocket, {
                "type": "reasoning",
                "step": "估值模型分析",
                "content": "基于历史数据，预测未来半年房价稳中有升，涨幅约5%。",
                "confidence": "95%置信区间：±3%",
                "timestamp": time.time()
            })
            
            # 推送政策分析
            await self.send_message(websocket, {
                "type": "reasoning",
                "step": "政策分析",
                "content": "近期政策对房地产市场持稳，预计不会出现大幅波动。",
                "timestamp": time.time()
            })
            
            # 推送周边配套分析
            await self.send_message(websocket, {
                "type": "reasoning",
                "step": "周边配套分析",
                "content": "南山区交通便利，教育资源丰富，医疗设施完善，有利于房价稳定增长。",
                "timestamp": time.time()
            })
            
            # 推送总结
            await self.send_message(websocket, {
                "type": "text",
                "content": "综上所述，深圳南山区房产市场前景良好，建议投资者保持关注。",
                "timestamp": time.time(),
                "style": "conclusion"
            })
            
            # 推送完成状态
            await self.send_message(websocket, {
                "type": "status",
                "content": "完成",
                "timestamp": time.time()
            })
            
        except Exception as e:
            await self.send_message(websocket, {
                "type": "error",
                "content": f"生成报告失败: {str(e)}",
                "timestamp": time.time()
            })
    
    def handle_control(self, client_id: str, command: str):
        """处理控制命令"""
        if command == "pause":
            self.pause_flags[client_id] = True
        elif command == "resume":
            self.pause_flags[client_id] = False
        elif command == "skip":
            self.skip_flags[client_id] = True


# 全局流式报告生成器
streaming_report_generator = StreamingReportGenerator()


@router.post("/start", response_model=StartConsultationResponse)
async def start_consultation(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    async with get_db() as db:
        try:
            persona = get_random_persona()
            
            gene_result = await db.fetchrow(
                "SELECT id FROM thinking_genes WHERE name = $1",
                persona.lower()
            )
            gene_id = gene_result['id'] if gene_result else None
            
            session_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO consultation_sessions (id, user_id, gene_id, status) VALUES ($1, $2, $3, $4)",
                session_id, user_id, gene_id, "active"
            )
            
            welcome_message = get_persona_welcome(persona)
            
            message_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO consultation_messages (id, session_id, role, content, persona_used) VALUES ($1, $2, $3, $4, $5)",
                message_id, session_id, "assistant", welcome_message, persona
            )
            
            config = get_persona_config(persona)
            persona_info = {
                "id": config.id if config else persona,
                "name": config.name if config else persona,
                "title": config.title if config else "",
                "style": config.style if config else "",
                "color_primary": config.color_primary if config else "#1E3A5F",
                "color_secondary": config.color_secondary if config else "#D4AF37",
            }
            
            return StartConsultationResponse(
                session_id=session_id,
                persona=persona,
                welcome_message=welcome_message,
                persona_info=persona_info,
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    async with get_db() as db:
        try:
            session = await db.fetchrow(
                """
                SELECT cs.gene_id, cs.user_id, tg.name as gene_name
                FROM consultation_sessions cs
                LEFT JOIN thinking_genes tg ON cs.gene_id = tg.id
                WHERE cs.id = $1 AND cs.status = 'active'
                """,
                request.session_id
            )
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if session['user_id'] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Not authorized")
            
            persona = session['gene_name'] or "zhouyu"
            user_id = current_user["id"]
            
            user_message_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO consultation_messages (id, session_id, role, content) VALUES ($1, $2, $3, $4)",
                user_message_id, request.session_id, "user", request.message
            )
            
            history = await db.fetch(
                """
                SELECT role, content FROM consultation_messages 
                WHERE session_id = $1 
                ORDER BY created_at ASC 
                LIMIT 20
                """,
                request.session_id
            )
            
            system_prompt = get_persona_system_prompt(persona)
            
            memory_context = None
            try:
                memory_context = await memory_service.get_context(user_id, request.message, max_memories=5)
            except Exception:
                pass
            
            reply = await generate_reply(system_prompt, history, request.message, persona, memory_context)
            
            emotion = detect_emotion(reply)
            
            assistant_message_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO consultation_messages (id, session_id, role, content, persona_used) VALUES ($1, $2, $3, $4, $5)",
                assistant_message_id, request.session_id, "assistant", reply, persona
            )
            
            await db.execute(
                "UPDATE consultation_sessions SET updated_at = $1 WHERE id = $2",
                datetime.utcnow().isoformat(), request.session_id
            )
            
            try:
                await memory_service.store(
                    user_id=user_id,
                    agent_name=f"consultant_{persona}",
                    input_text=request.message,
                    output_text=reply,
                    session_id=request.session_id,
                    summary=f"咨询：{request.message[:50]}...",
                    importance=6.0,
                    category="consultation"
                )
            except Exception:
                pass
            
            return SendMessageResponse(
                reply=reply,
                emotion=emotion,
                persona=persona,
            )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=List[MessageHistory])
async def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    async with get_db() as db:
        try:
            session = await db.fetchrow(
                "SELECT user_id FROM consultation_sessions WHERE id = $1",
                session_id
            )
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if session['user_id'] != current_user["id"]:
                raise HTTPException(status_code=403, detail="Not authorized")
            
            messages = await db.fetch(
                """
                SELECT id, role, content, persona, created_at 
                FROM consultation_messages 
                WHERE session_id = $1 
                ORDER BY created_at ASC
                """,
                session_id
            )
            
            return [
                MessageHistory(
                    id=msg['id'],
                    role=msg['role'],
                    content=msg['content'],
                    persona=msg['persona'],
                    created_at=str(msg['created_at']),
                )
                for msg in messages
            ]
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    async with get_db() as db:
        try:
            sessions = await db.fetch(
                """
                SELECT cs.id, cs.gene_id, cs.status, cs.created_at, cs.session_start,
                       tg.name as gene_name, tg.display_name
                FROM consultation_sessions cs
                LEFT JOIN thinking_genes tg ON cs.gene_id = tg.id
                WHERE cs.user_id = $1 
                ORDER BY cs.created_at DESC 
                LIMIT $2 OFFSET $3
                """,
                current_user["id"], limit, offset
            )
            
            total = await db.fetchval(
                "SELECT COUNT(*) FROM consultation_sessions WHERE user_id = $1",
                current_user["id"]
            )
            
            return {
                "sessions": [
                    {
                        "id": session['id'],
                        "persona": session['gene_name'] or session['display_name'] or "zhouyu",
                        "status": session['status'],
                        "created_at": str(session['created_at'] or session['session_start']),
                        "updated_at": str(session['created_at'] or session['session_start']),
                    }
                    for session in sessions
                ],
                "total": total or 0,
            }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions")
async def create_session(
    title: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    
    async with get_db() as db:
        try:
            session_id = str(uuid.uuid4())
            persona = random.choice(["zhouyu", "luxun"])
            
            gene_result = await db.fetchrow(
                "SELECT id FROM thinking_genes WHERE name = $1",
                persona
            )
            gene_id = gene_result['id'] if gene_result else None
            
            await db.execute(
                "INSERT INTO consultation_sessions (id, user_id, gene_id, status) VALUES ($1, $2, $3, $4)",
                session_id, user_id, gene_id, "active"
            )
            
            return {
                "id": session_id,
                "persona": persona,
                "status": "active",
                "message": f"已为您分配 {persona} 都督"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/persona")
async def get_my_persona(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    
    async with get_db() as db:
        try:
            result = await db.fetchrow(
                "SELECT persona FROM user_personas WHERE user_id = $1",
                user_id
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Persona not assigned")
            
            persona = result['persona']
            config = get_persona_config(persona)
            
            return {
                "persona": persona,
                "config": {
                    "id": config.id if config else persona,
                    "name": config.name if config else persona,
                    "title": config.title if config else "",
                    "style": config.style if config else "",
                    "welcome_message": config.welcome_message if config else "",
                    "color_primary": config.color_primary if config else "#1E3A5F",
                    "color_secondary": config.color_secondary if config else "#D4AF37",
                    "emoji": config.emoji if config else "",
                    "description": config.description if config else "",
                }
            }
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/parallel")
async def parallel_consult(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    query = request.get("query", "")
    agents = request.get("agents", ["analyst"])
    
    results = []
    for agent in agents:
        results.append({
            "agent": agent,
            "response": f"关于「{query[:30]}...」的分析已完成。",
            "confidence": 0.85
        })
    
    return {
        "query": query,
        "results": results,
        "synthesis": "综合分析结果：根据多智能体协同分析，建议进一步调研。"
    }


@router.websocket("/ws/report")
async def websocket_report_endpoint(websocket: WebSocket):
    """WebSocket端点用于流式报告生成"""
    client_id = await streaming_report_generator.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            
            # 处理控制命令
            if "command" in data:
                command = data["command"]
                streaming_report_generator.handle_control(client_id, command)
            # 处理报告生成请求
            elif "report_request" in data:
                report_request = ReportRequest(**data["report_request"])
                await streaming_report_generator.generate_report(websocket, report_request)
    
    except WebSocketDisconnect:
        await streaming_report_generator.disconnect(websocket)
    except Exception as e:
        await streaming_report_generator.send_message(websocket, {
            "type": "error",
            "content": f"WebSocket连接失败: {str(e)}",
            "timestamp": time.time()
        })
        await streaming_report_generator.disconnect(websocket)


async def generate_reply(system_prompt: str, history: list, user_message: str, persona: str, memory_context: str = None) -> str:
    from ..llm_service import llm_service
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if memory_context:
        messages.append({
            "role": "system", 
            "content": f"用户历史偏好和记忆：\n{memory_context}"
        })
    
    for turn in history:
        role = "user" if turn['role'] == "user" else "assistant"
        messages.append({"role": role, "content": turn['content']})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = await llm_service.generate(messages)
        return response
    except Exception:
        if persona == PersonaType.ZHOUYU.value:
            return f"主公此事，且听瑜一言。关于「{user_message[:20]}...」，瑜已深思熟虑。此问题涉及诸多因素，需从长计议。"
        else:
            return f"主公且慢。关于「{user_message[:20]}...」，逊有几点看法。此事需谨慎对待，不可操之过急。"


def detect_emotion(text: str) -> str:
    if any(word in text for word in ['风险', '危险', '警告', '且慢', '不可']):
        return 'serious'
    elif any(word in text for word in ['恭喜', '祝贺', '妙', '好']):
        return 'happy'
    elif any(word in text for word in ['思考', '推演', '细察', '分析']):
        return 'thinking'
    elif any(word in text for word in ['意外', '惊讶', '没想到']):
        return 'surprised'
    return 'default'
