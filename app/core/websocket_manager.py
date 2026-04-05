from typing import Dict, List, Optional, Any
import json
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        # 存储活动的WebSocket连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储连接的订阅关系
        self.subscriptions: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = ["*"]  # 默认订阅所有事件
        print(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected")
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {client_id}: {str(e)}")
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def broadcast_to_subscribers(self, message: Dict[str, Any], event_type: str):
        """Broadcast a message to subscribers of a specific event type"""
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            # 检查客户端是否订阅了该事件类型或所有事件
            if event_type in self.subscriptions.get(client_id, []) or "*" in self.subscriptions.get(client_id, []):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to {client_id}: {str(e)}")
                    disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def subscribe(self, client_id: str, event_type: str):
        """Subscribe a client to an event type"""
        if client_id in self.subscriptions:
            if event_type not in self.subscriptions[client_id]:
                self.subscriptions[client_id].append(event_type)
                print(f"Client {client_id} subscribed to {event_type}")
    
    def unsubscribe(self, client_id: str, event_type: str):
        """Unsubscribe a client from an event type"""
        if client_id in self.subscriptions:
            if event_type in self.subscriptions[client_id]:
                self.subscriptions[client_id].remove(event_type)
                print(f"Client {client_id} unsubscribed from {event_type}")


# 创建全局WebSocket连接管理器
manager = ConnectionManager()
