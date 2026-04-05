"""
流式报告生成系统
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


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
        logger.info(f"新客户端连接: {client_id}")
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
        logger.info(f"客户端断开: {client_id}")
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """发送消息"""
        try:
            await websocket.send_json(message)
            await asyncio.sleep(0.05)  # 控制发送速度
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    async def check_pause(self, client_id: str):
        """检查是否暂停"""
        while self.pause_flags.get(client_id, False):
            await asyncio.sleep(0.1)
    
    async def generate_report(self, websocket: WebSocket, request: ReportRequest):
        """生成报告"""
        client_id = f"client_{id(websocket)}"
        
        try:
            # 步骤S3: 推送报告标题
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
            
            # 步骤S4: 推送图表框架
            await self.send_message(websocket, {
                "type": "chart",
                "chartType": "line",
                "title": "近一年房价走势",
                "xAxis": "月份",
                "yAxis": "均价（元/㎡）",
                "partial": False,
                "timestamp": time.time()
            })
            
            # 推送数据点
            months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
                     "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
            prices = [95000, 96000, 97000, 96500, 97500, 98000,
                     98500, 99000, 99500, 100000, 100500, 101000]
            
            for month, price in zip(months, prices):
                # 检查是否暂停
                await self.check_pause(client_id)
                
                # 检查是否跳过
                if self.skip_flags.get(client_id, False):
                    break
                
                await self.send_message(websocket, {
                    "type": "chart",
                    "chartType": "line",
                    "data": {"x": month, "y": price},
                    "partial": True,
                    "timestamp": time.time()
                })
                await asyncio.sleep(0.5)  # 控制绘制速度
            
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
            
            # 步骤S5: 推送推理步骤
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
            
            # 步骤S7: 推送完成状态
            await self.send_message(websocket, {
                "type": "status",
                "content": "完成",
                "timestamp": time.time()
            })
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            await self.send_message(websocket, {
                "type": "error",
                "content": f"生成报告失败: {str(e)}",
                "timestamp": time.time()
            })
    
    def handle_control(self, client_id: str, command: str):
        """处理控制命令"""
        if command == "pause":
            self.pause_flags[client_id] = True
            logger.info(f"客户端 {client_id} 暂停")
        elif command == "resume":
            self.pause_flags[client_id] = False
            logger.info(f"客户端 {client_id} 继续")
        elif command == "skip":
            self.skip_flags[client_id] = True
            logger.info(f"客户端 {client_id} 跳过")


# 全局流式报告生成器
streaming_report_generator = StreamingReportGenerator()


# 创建FastAPI应用
app = FastAPI(title="流式报告生成系统")


@app.websocket("/ws/report")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    client_id = await streaming_report_generator.connect(websocket)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 处理控制命令
            if data.get("type") == "control":
                command = data.get("command")
                streaming_report_generator.handle_control(client_id, command)
            
            # 处理报告请求
            elif data.get("type") == "request":
                request = ReportRequest(**data.get("request", {}))
                # 异步生成报告
                asyncio.create_task(streaming_report_generator.generate_report(websocket, request))
                
    except WebSocketDisconnect:
        await streaming_report_generator.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        await streaming_report_generator.disconnect(websocket)


@app.post("/api/report/generate")
async def generate_report(request: ReportRequest):
    """生成报告API"""
    # 这里返回WebSocket连接信息
    return {
        "message": "请通过WebSocket连接获取流式报告",
        "websocket_url": "ws://localhost:8000/ws/report",
        "request": request.dict()
    }


@app.get("/api/report/status")
async def get_report_status():
    """获取报告状态"""
    return {
        "active_connections": len(streaming_report_generator.active_connections),
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "streaming_report:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
