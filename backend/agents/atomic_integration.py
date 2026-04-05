"""
思维原子系统集成模块
将思维原子系统集成到房都督平台的智能体集群中
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.agents.atomic_agent import process_text, process_query
from backend.agents.atomic_library import get_all_atoms, update_atom_weight
from backend.agents.atomic_injector import process_user_feedback

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="思维原子系统API",
    description="基于思维原子的智能体决策系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/atomic/extract")
async def extract_atoms(text: str):
    """提取思维原子
    
    Args:
        text: 用户上传的文本
        
    Returns:
        提取的思维原子
    """
    try:
        result = await process_text(text)
        return result
    except Exception as e:
        logger.error(f"提取思维原子失败: {e}")
        raise HTTPException(status_code=500, detail="提取思维原子失败")


@app.post("/api/atomic/query")
async def query_with_atoms(query: str):
    """使用思维原子处理查询
    
    Args:
        query: 用户查询
        
    Returns:
        处理结果
    """
    try:
        result = await process_query(query)
        return result
    except Exception as e:
        logger.error(f"处理查询失败: {e}")
        raise HTTPException(status_code=500, detail="处理查询失败")


@app.get("/api/atomic/library")
async def get_atomic_library():
    """获取思维原子库
    
    Returns:
        思维原子库中的所有原子
    """
    try:
        atoms = get_all_atoms()
        return {
            "atoms": [
                {
                    "name": atom.name,
                    "description": atom.description,
                    "keywords": atom.keywords,
                    "scenario": atom.scenario,
                    "weight": atom.weight
                }
                for atom in atoms
            ],
            "count": len(atoms)
        }
    except Exception as e:
        logger.error(f"获取原子库失败: {e}")
        raise HTTPException(status_code=500, detail="获取原子库失败")


@app.post("/api/atomic/feedback")
async def atom_feedback(atom_id: str, is_useful: bool):
    """处理用户反馈
    
    Args:
        atom_id: 原子ID
        is_useful: 是否有用
        
    Returns:
        处理结果
    """
    try:
        process_user_feedback(atom_id, is_useful)
        return {"message": "反馈处理成功"}
    except Exception as e:
        logger.error(f"处理反馈失败: {e}")
        raise HTTPException(status_code=500, detail="处理反馈失败")


@app.post("/api/atomic/update_weight")
async def update_weight(atom_id: str, weight: float):
    """更新思维原子权重
    
    Args:
        atom_id: 原子ID
        weight: 新权重
        
    Returns:
        处理结果
    """
    try:
        update_atom_weight(atom_id, weight)
        return {"message": "权重更新成功"}
    except Exception as e:
        logger.error(f"更新权重失败: {e}")
        raise HTTPException(status_code=500, detail="更新权重失败")


@app.get("/api/atomic/health")
async def health_check():
    """健康检查
    
    Returns:
        健康状态
    """
    return {"status": "healthy", "service": "atomic-agent"}


class AtomicIntegration:
    """思维原子系统集成类"""
    
    def __init__(self):
        self.api_app = app
    
    def start_api(self, host: str = "0.0.0.0", port: int = 8000):
        """启动API服务器
        
        Args:
            host: 主机地址
            port: 端口号
        """
        logger.info(f"启动思维原子系统API服务器: http://{host}:{port}")
        uvicorn.run(self.api_app, host=host, port=port)
    
    def integrate_with_agent(self, agent):
        """与智能体集成
        
        Args:
            agent: 智能体实例
        """
        # 这里可以实现与智能体的集成逻辑
        # 例如，为智能体添加思维原子注入功能
        logger.info("将思维原子系统集成到智能体中")
        
        # 为智能体添加原子注入方法
        async def process_with_atoms(self, query):
            """使用思维原子处理查询"""
            result = await process_query(query)
            return result
        
        # 动态添加方法到智能体
        agent.process_with_atoms = process_with_atoms.__get__(agent)
        logger.info("智能体集成完成")
    
    def get_integration_config(self) -> Dict[str, Any]:
        """获取集成配置
        
        Returns:
            集成配置
        """
        return {
            "api_endpoints": {
                "extract": "/api/atomic/extract",
                "query": "/api/atomic/query",
                "library": "/api/atomic/library",
                "feedback": "/api/atomic/feedback",
                "update_weight": "/api/atomic/update_weight",
                "health": "/api/atomic/health"
            },
            "integration_points": [
                "agent_processing",
                "user_feedback",
                "decision_making"
            ],
            "requirements": [
                "fastapi",
                "uvicorn",
                "numpy"
            ]
        }


# 全局集成实例
atomic_integration: Optional[AtomicIntegration] = None


def get_atomic_integration() -> AtomicIntegration:
    """获取集成实例"""
    global atomic_integration
    if atomic_integration is None:
        atomic_integration = AtomicIntegration()
    return atomic_integration


def start_atomic_api(host: str = "0.0.0.0", port: int = 8000):
    """启动思维原子系统API"""
    integration = get_atomic_integration()
    integration.start_api(host, port)


def integrate_with_agent(agent):
    """与智能体集成"""
    integration = get_atomic_integration()
    integration.integrate_with_agent(agent)


def get_integration_config() -> Dict[str, Any]:
    """获取集成配置"""
    integration = get_atomic_integration()
    return integration.get_integration_config()


if __name__ == "__main__":
    # 启动API服务器
    start_atomic_api()
