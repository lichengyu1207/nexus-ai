"""
高级对话API
使用真正的智能体系统进行并行处理
集成仪表盘的现有业务逻辑
集成Token两阶段消耗
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid
import json
import asyncio

from ..auth import get_current_user
from ..database import get_db_connection
from ..agents import (
    AgentScheduler,
    InputProcessorAgent,
    DialogueSupervisorAgent,
    RequirementAgent,
    CollectorAgent
)
from ..services.token_service import token_service
from ..utils.token_counter import count_tokens

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dialogue", tags=["高级对话"])


class DialogueRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    is_binary: bool = False


class DialogueResponse(BaseModel):
    session_id: str
    user_input: str
    binary_input: str
    decoded_input: str
    steps: List[Dict[str, Any]]
    agent_assignments: List[Dict[str, Any]]
    keywords_matched: List[Dict[str, Any]]
    missing_info: List[Dict[str, Any]]
    final_response: str
    binary_response: str
    needs_follow_up: bool
    follow_up_question: Optional[str]
    info_collected: bool
    collected_count: int
    created_at: str


async def save_message(session_id: str, user_id: str, role: str, content: str, intent: str = None, entities: dict = None):
    """保存消息到数据库"""
    conn = await get_db_connection()
    try:
        message_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO dialogue_history (id, session_id, user_id, role, content, intent, entities, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [message_id, session_id, user_id, role, content, intent, json.dumps(entities) if entities else None, datetime.now().isoformat()]
        )
        await conn.commit()
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
    finally:
        await conn.close()


async def load_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """加载对话历史"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT role, content, intent, entities, created_at
            FROM dialogue_history
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [session_id, limit]
        )
        rows = await cursor.fetchall()
        history = []
        for row in reversed(rows):
            history.append({
                "role": row["role"],
                "content": row["content"],
                "intent": row["intent"],
                "entities": json.loads(row["entities"]) if row["entities"] else None,
                "created_at": row["created_at"]
            })
        return history
    except Exception as e:
        logger.error(f"Failed to load history: {e}")
        return []
    finally:
        await conn.close()


async def get_or_create_session(session_id: Optional[str], user_id: str) -> str:
    """获取或创建会话"""
    conn = await get_db_connection()
    try:
        if session_id:
            cursor = await conn.execute(
                "SELECT id FROM dialogue_sessions WHERE id = ? AND user_id = ?",
                [session_id, user_id]
            )
            row = await cursor.fetchone()
            if row:
                return session_id
        
        new_session_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO dialogue_sessions (id, user_id, status, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?)
            """,
            [new_session_id, user_id, datetime.now().isoformat(), datetime.now().isoformat()]
        )
        await conn.commit()
        return new_session_id
    except Exception as e:
        logger.error(f"Failed to get/create session: {e}")
        return session_id or str(uuid.uuid4())
    finally:
        await conn.close()


async def update_session_keywords(session_id: str, keywords: Dict[str, Any]):
    """更新会话已收集的关键词"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT collected_keywords FROM dialogue_sessions WHERE id = ?",
            [session_id]
        )
        row = await cursor.fetchone()
        
        existing = {}
        if row and row["collected_keywords"]:
            existing = json.loads(row["collected_keywords"])
        
        existing.update(keywords)
        
        await conn.execute(
            """
            UPDATE dialogue_sessions 
            SET collected_keywords = ?, updated_at = ?
            WHERE id = ?
            """,
            [json.dumps(existing), datetime.now().isoformat(), session_id]
        )
        await conn.commit()
    except Exception as e:
        logger.error(f"Failed to update keywords: {e}")
    finally:
        await conn.close()


async def get_session_keywords(session_id: str) -> Dict[str, Any]:
    """获取会话已收集的关键词"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT collected_keywords FROM dialogue_sessions WHERE id = ?",
            [session_id]
        )
        row = await cursor.fetchone()
        if row and row["collected_keywords"]:
            return json.loads(row["collected_keywords"])
        return {}
    except Exception as e:
        logger.error(f"Failed to get keywords: {e}")
        return {}
    finally:
        await conn.close()


async def run_dialogue_workflow(task_id: str, user_input: str, is_binary: bool, collected_keywords: Dict[str, Any]) -> Dict[str, Any]:
    """
    运行对话智能体工作流
    集成仪表盘的现有业务逻辑
    优化后的异步处理逻辑
    """
    try:
        scheduler = AgentScheduler(task_id, db_enabled=True, sse_enabled=False)
        
        supervisor = scheduler.register_agent(DialogueSupervisorAgent, "dialogue_supervisor")
        scheduler.register_agent(InputProcessorAgent, "input_processor")
        scheduler.register_agent(RequirementAgent, "requirement")
        scheduler.register_agent(CollectorAgent, "collector")
        
        await scheduler.start_all()
        
        await asyncio.sleep(0.2)
        
        from ..agents.message import AgentMessage, MessageType
        
        msg = AgentMessage(
            task_id=task_id,
            sender="api",
            recipient="dialogue_supervisor",
            type=MessageType.REQUEST,
            content={
                "action": "start",
                "query": user_input,
                "is_binary": is_binary,
                "collected_keywords": collected_keywords
            }
        )
        
        await supervisor.bus.publish(msg)
        
        completed = await supervisor.wait_for_result(timeout=30.0)
        
        result = supervisor.get_workflow_result()
        
        await scheduler.stop_all()
        
        if not result:
            return {"status": "error", "message": "工作流执行超时"}
        
        return result
        
    except Exception as e:
        logger.error(f"Dialogue workflow failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/process", response_model=DialogueResponse)
async def process_dialogue(
    request: DialogueRequest,
    user: dict = Depends(get_current_user)
):
    """
    处理对话消息 - 使用真正的智能体系统并行处理
    
    流程：
    1. 预扣Token（两阶段消耗第一阶段）
    2. InputProcessorAgent - 输入处理（二进制转换）
    3. RequirementAgent - 需求解析（仪表盘业务逻辑）
    4. CollectorAgent - 数据采集（仪表盘业务逻辑）
    5. DialogueSupervisorAgent - 协调整个流程
    6. 确认Token消耗（两阶段消耗第二阶段）或回滚
    """
    reservation_id = None
    
    try:
        user_id = user.get('id')
        session_id = await get_or_create_session(request.session_id, user_id)
        
        collected_keywords = await get_session_keywords(session_id)
        
        input_tokens = count_tokens(request.message)
        estimated_output_tokens = int(input_tokens * 0.5)
        estimated_total = input_tokens + estimated_output_tokens
        
        reserve_result = await token_service.reserve_tokens(
            user_id=user_id,
            action_type="dialogue",
            estimated_tokens=estimated_total,
            metadata={
                "session_id": session_id,
                "input_preview": request.message[:100]
            }
        )
        
        if not reserve_result.get("success"):
            raise HTTPException(
                status_code=402,
                detail=f"积分不足: {reserve_result.get('error', '预扣失败')}"
            )
        
        reservation_id = reserve_result.get("reservation_id")
        logger.info(f"Token reserved for dialogue: {reservation_id}, tokens={estimated_total}")
        
        task_id = str(uuid.uuid4())
        
        result = await run_dialogue_workflow(
            task_id=task_id,
            user_input=request.message,
            is_binary=request.is_binary,
            collected_keywords=collected_keywords
        )
        
        if result.get("status") == "error":
            rollback_result = await token_service.rollback_reservation(
                reservation_id=reservation_id,
                reason=f"对话处理失败: {result.get('message', '未知错误')}"
            )
            logger.info(f"Token rolled back due to error: {reservation_id}")
            raise HTTPException(status_code=500, detail=result.get("message", "处理失败"))
        
        decoded_input = result.get("decoded_input", request.message)
        final_response = result.get("response", "抱歉，我无法处理您的请求。")
        
        output_tokens = count_tokens(final_response)
        
        confirm_result = await token_service.confirm_consumption(
            reservation_id=reservation_id,
            input_text=decoded_input,
            output_text=final_response
        )
        
        if confirm_result.get("success"):
            logger.info(f"Token consumption confirmed: {reservation_id}, actual_tokens={confirm_result.get('actual_tokens')}")
        else:
            logger.warning(f"Token confirmation failed: {confirm_result.get('error')}")
        
        await save_message(
            session_id=session_id,
            user_id=user_id,
            role='user',
            content=decoded_input
        )
        
        await save_message(
            session_id=session_id,
            user_id=user_id,
            role='assistant',
            content=final_response,
            entities={"keywords": result.get("keywords", {})}
        )
        
        if result.get("keywords"):
            await update_session_keywords(session_id, result.get("keywords"))
        
        if result.get("collected_keywords"):
            await update_session_keywords(session_id, result.get("collected_keywords"))
        
        steps = []
        message_history = []
        try:
            from ..database import AgentMessageDB
            message_history = await AgentMessageDB.get_messages_by_task(task_id)
        except:
            pass
        
        for msg in message_history:
            if msg.get("content", {}).get("event") == "step":
                step_data = msg["content"]["step"]
                steps.append({
                    "step_id": step_data.get("id", ""),
                    "step_name": step_data.get("step_name", ""),
                    "step_type": step_data.get("agent_name", ""),
                    "status": step_data.get("status", "completed"),
                    "input_data": step_data.get("input_data", {}),
                    "output_data": step_data.get("output_data", {}),
                    "duration_ms": 0,
                    "timestamp": step_data.get("created_at", "")
                })
        
        token_info = {
            "input_tokens": confirm_result.get("actual_tokens", 0) if confirm_result.get("success") else estimated_total,
            "cost_integral": confirm_result.get("actual_cost", 0) if confirm_result.get("success") else reserve_result.get("cost_integral", 0),
            "balance_after": confirm_result.get("balance_after", 0) if confirm_result.get("success") else reserve_result.get("balance_after", 0)
        }
        
        return DialogueResponse(
            session_id=session_id,
            user_input=request.message[:200],
            binary_input=result.get("binary_input", "")[:500],
            decoded_input=decoded_input,
            steps=steps,
            agent_assignments=result.get("agents", []),
            keywords_matched=[{"keyword": k, "value": v, "category": "extracted", "confidence": 1.0} for k, v in result.get("keywords", {}).items()],
            missing_info=result.get("missing_info", []),
            final_response=final_response,
            binary_response=result.get("binary_response", ""),
            needs_follow_up=result.get("needs_follow_up", False),
            follow_up_question=result.get("follow_up_question"),
            info_collected=result.get("info_collected", False),
            collected_count=result.get("collected_count", 0),
            created_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if reservation_id:
            try:
                await token_service.rollback_reservation(
                    reservation_id=reservation_id,
                    reason=f"系统异常: {str(e)}"
                )
                logger.info(f"Token rolled back due to exception: {reservation_id}")
            except Exception as rb_error:
                logger.error(f"Rollback failed: {rb_error}")
        
        logger.error(f"Dialogue processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_available_agents():
    """获取可用的智能体列表"""
    return {
        "agents": [
            {"id": "property_analyst", "name": "房产分析师", "capabilities": ["房价分析", "市场趋势", "投资建议"]},
            {"id": "area_expert", "name": "区域专家", "capabilities": ["区域介绍", "周边配套", "交通分析"]},
            {"id": "loan_advisor", "name": "贷款顾问", "capabilities": ["贷款计算", "利率分析", "还款方案"]},
            {"id": "policy_expert", "name": "政策专家", "capabilities": ["购房政策", "限购限贷", "税费计算"]},
            {"id": "community_guide", "name": "小区向导", "capabilities": ["小区介绍", "房源推荐", "户型分析"]}
        ]
    }


@router.get("/required-fields")
async def get_required_fields():
    """获取需要收集的字段列表"""
    return {
        "fields": {
            "high": [
                {"field": "city", "label": "城市", "question": "您想在哪个城市购房?"},
                {"field": "price_max", "label": "预算", "question": "您的购房预算大概是多少?"}
            ],
            "medium": [
                {"field": "room_count", "label": "户型", "question": "您需要几室几厅的房子?"},
                {"field": "district", "label": "区域", "question": "您有偏好的区域吗?"}
            ],
            "low": [
                {"field": "area_min", "label": "面积", "question": "您对面积有什么要求?"},
                {"field": "orientation", "label": "朝向", "question": "您对朝向有要求吗?"}
            ]
        }
    }
