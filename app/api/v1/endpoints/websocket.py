from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, Dict, Any
import uuid
from app.core.websocket_manager import manager
from app.ai_agents.event_system import event_manager

router = APIRouter()


@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket endpoint for real-time event streaming"""
    # 如果没有提供client_id，生成一个
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # 接受连接
    await manager.connect(websocket, client_id)
    
    # 定义事件处理函数
    async def handle_event(event: Dict[str, Any]):
        await manager.send_personal_message(event, client_id)
    
    # 订阅事件
    event_manager.subscribe("*", handle_event)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            
            # 处理客户端消息
            if "action" in data:
                action = data["action"]
                if action == "subscribe":
                    # 订阅特定事件类型
                    event_type = data.get("event_type", "*")
                    manager.subscribe(client_id, event_type)
                elif action == "unsubscribe":
                    # 取消订阅特定事件类型
                    event_type = data.get("event_type", "*")
                    manager.unsubscribe(client_id, event_type)
                elif action == "ping":
                    # 响应心跳
                    await manager.send_personal_message({"type": "pong"}, client_id)
                elif action == "pause":
                    # 暂停工作流
                    task_id = data.get("task_id")
                    if task_id:
                        # 这里应该实现暂停工作流的逻辑
                        print(f"收到暂停工作流命令: {task_id}")
                        # 发布工作流暂停事件
                        from app.ai_agents.event_system import AgentEvent
                        pause_event = AgentEvent(
                            event_type="workflow_pause",
                            agent_id=task_id,
                            agent_name="用户"
                        )
                        pause_event.payload = {
                            "task_id": task_id,
                            "message": "工作流已暂停"
                        }
                        event_manager.publish(pause_event)
                elif action == "resume":
                    # 恢复工作流
                    task_id = data.get("task_id")
                    if task_id:
                        print(f"收到恢复工作流命令: {task_id}")
                        # 发布工作流恢复事件
                        from app.ai_agents.event_system import AgentEvent
                        resume_event = AgentEvent(
                            event_type="workflow_resume",
                            agent_id=task_id,
                            agent_name="用户"
                        )
                        resume_event.payload = {
                            "task_id": task_id,
                            "message": "工作流已恢复"
                        }
                        event_manager.publish(resume_event)
                elif action == "cancel":
                    # 取消工作流
                    task_id = data.get("task_id")
                    if task_id:
                        print(f"收到取消工作流命令: {task_id}")
                        # 发布工作流取消事件
                        from app.ai_agents.event_system import AgentEvent
                        cancel_event = AgentEvent(
                            event_type="workflow_cancel",
                            agent_id=task_id,
                            agent_name="用户"
                        )
                        cancel_event.payload = {
                            "task_id": task_id,
                            "message": "工作流已取消"
                        }
                        event_manager.publish(cancel_event)
                elif action == "ask_question":
                    # 向智能体提问
                    task_id = data.get("task_id")
                    agent_id = data.get("agent_id")
                    question = data.get("question")
                    if task_id and agent_id and question:
                        print(f"收到向智能体提问命令: 任务ID={task_id}, 智能体ID={agent_id}, 问题={question}")
                        # 发布智能体提问事件
                        from app.ai_agents.event_system import AgentEvent
                        question_event = AgentEvent(
                            event_type="agent_question",
                            agent_id=agent_id,
                            agent_name="用户"
                        )
                        question_event.payload = {
                            "task_id": task_id,
                            "question": question,
                            "message": f"用户向{agent_id}提问: {question}"
                        }
                        event_manager.publish(question_event)
    except WebSocketDisconnect:
        # 断开连接时清理
        event_manager.unsubscribe("*", handle_event)
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        event_manager.unsubscribe("*", handle_event)
        manager.disconnect(client_id)


@router.get("/ws/connections")
async def get_connections():
    """Get the number of active WebSocket connections"""
    return {
        "active_connections": len(manager.active_connections),
        "subscriptions": manager.subscriptions
    }
