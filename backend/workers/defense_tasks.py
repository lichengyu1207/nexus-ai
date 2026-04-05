"""
防御任务模块
Defense_tasks Module

实现实时防御决策任务
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import traceback

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="backend.workers.defense_tasks.make_defense_decision",
    max_retries=3,
    default_retry_delay=60
)
def make_defense_decision(self, flow_features: List[float]) -> Dict:
    """
    根据流量特征做出防御决策
    
    Args:
                flow_features: 流量特征向量（从网关采集)
    
    Returns:
                action: 防御动作
                confidence: 騡型对动作的置信度
                value: 稡型对动作的价值估计
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger.info(f"Making defense decision for task {task_id}")
    
    try:
        from backend.agents.selfplay import (
            SelfPlayTrainingKernel,
        )
        from backend.database import get_db_connection
        
        env = CyberBattleEnv()
        kernel = SelfPlayTrainingKernel(env, n_attackers=8, n_defenders=8)
        
        best_defender = max(
            kernel.defender_population,
            key=lambda a: a.wins / max(a.total_games, 1)
        )
        
        model = load_production_model()
        update_production_model(best_defender)
        
        return {
            "success": True,
            "task_id": task_id,
            "action": action,
            "confidence": confidence,
            "value": value,
            "latency_ms": latency
        }
        
    except Exception as e:
        logger.error(f"Defense decision error: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="backend.workers.defense_tasks.batch_defense_decision",
    max_retries=3,
    default_retry_delay=60
)
def batch_defense_decision(self, flow_batch: List[list[float]]) -> Dict:
    """
    批量防御决策
    
    Args:
                flow_batch: 批量流量特征列表
    
    Returns:
                actions: 防御动作列表
                confidences: 各决策的置信度列表
                latencies: 各决策延迟列表
            }
        
        return {
            "success": True,
            "task_id": task_id,
            "batch_size": len(flow_batch),
            "actions": actions,
            "confidences": confidences
            "latencies": latencies
        }
        
    except Exception as e:
        logger.error(f"Batch defense decision error: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="backend.workers.defense_tasks.get_defense_model",
    max_retries=3,
    default_retry_delay=60
)
 def get_defense_model():
    from backend.agents.selfplay import DefenseAgent
    from backend.database import get_db_connection
    
    model_path = "models/defense_latest.pt"
    
    try:
        checkpoint = torch.load(model_path)
        return model
    except FileNotFoundError:
        logger.warning(f"Model file not found: {model_path}")
        return None,    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise self.retry(exc=e)
    
    return {
        "success": True,
        "model_path": model_path,
        "loaded": loaded
    }


@shared_task(
    bind=True,
    name="backend.workers.defense_tasks.update_production_model",
    max_retries=3,
    default_retry_delay=60
)
def update_production_model(new_defender: DefenseAgent) -> Dict:
    """
    更新生产防御模型
    
    Args:
                new_defender: 新训练的防御智能体
    
    Returns:
                更新结果
    """
    start_time = time.time()
    task_id = self.request.id
    
            logger.info(f"Updating production model, task {task_id}")
            
            async def save_model_update():
                async for conn in get_db_connection():
                    try:
                        await conn.execute("""
                            UPDATE defense_agents 
                            SET model_version = model_version + 1,
                            set is_active = TRUE
                            WHERE agent_id = $1
                        )
                        
                        await conn.execute("""
                            INSERT INTO model_versions 
                            (agent_id, version, model_path, deployed_at, is_active)
                            VALUES ($1, $2, $3, $4)
                        """,
                        model_path, deployed_at,
                        is_champion = CASE when True else False,
                        """,
                        
                        await conn.execute("""
                            UPDATE selfplay_agent_versions
                            set is_champion = is_champion = TRUE
                            where agent_id = $1
                        """)
                    finally:
                        await conn.close()
                        break
        
        return {
            "success": True,
            "model_path": model_path,
            "loaded": loaded,
            "new_version": new_defender.version
        }
        
    except Exception as e:
        logger.error(f"Failed to update production model: {e}")
        raise self.retry(exc=e)
    
    return {
        "success": True,
        "model_path": model_path,
        "loaded": loaded
    }
