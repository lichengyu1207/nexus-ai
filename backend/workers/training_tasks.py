"""
训练任务模块
Training Tasks Module

实现自博弈训练、模型更新等后台任务
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import traceback

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="backend.workers.training_tasks.self_play_training_cycle",
    max_retries=3,
    default_retry_delay=60
)
def self_play_training_cycle(self, num_episodes: int = 1000) -> Dict:
    """
    自博弈训练一轮
    
    Args:
        num_episodes: 每轮训练的对局数
    
    Returns:
        训练结果统计
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger.info(f"Starting self-play training cycle: {num_episodes} episodes")
    
    try:
        from backend.agents.selfplay import (
            SelfPlayTrainingKernel,
            CyberBattleEnv,
            SelfPlayTrainer,
            NetworkSecurityEnv
        )
        from backend.database import get_db_connection
        
        env = CyberBattleEnv()
        kernel = SelfPlayTrainingKernel(env, n_attackers=8, n_defenders=8)
        
        results = []
        update_interval = 10
        
        for episode in range(num_episodes):
            try:
                result = kernel.train_step(update_interval)
                results.append(result)
                
                if episode % 100 == 0:
                    logger.info(f"Training progress: {episode}/{num_episodes} episodes")
                    
            except Exception as e:
                logger.error(f"Error in episode {episode}: {e}")
                continue
        
        best_defender = max(
            kernel.defender_population,
            key=lambda a: a.wins / max(a.total_games, 1)
        )
        
        model_dir = "models/trained"
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f"defense_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt")
        
        import torch
        torch.save(best_defender.policy.state_dict(), model_path)
        
        champion_path = os.path.join(model_dir, "defense_latest.pt")
        torch.save(best_defender.policy.state_dict(), champion_path)
        
        async def save_training_result():
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        INSERT INTO training_sessions 
                        (session_id, start_time, end_time, num_episodes, 
                         best_defender_id, best_win_rate, model_path, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, 'completed')
                    """,
                        task_id,
                        datetime.fromtimestamp(start_time),
                        datetime.now(),
                        num_episodes,
                        best_defender.agent_id,
                        best_defender.wins / max(best_defender.total_games, 1),
                        model_path
                    )
                    
                    await conn.execute("""
                        INSERT INTO model_versions 
                        (model_type, version, path, win_rate, is_active, created_at)
                        VALUES ('defense', 
                                (SELECT COALESCE(MAX(version), 0) + 1 FROM model_versions WHERE model_type = 'defense'),
                                $1, $2, TRUE, CURRENT_TIMESTAMP)
                    """, model_path, best_defender.wins / max(best_defender.total_games, 1))
                finally:
                    await conn.close()
                    break
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(save_training_result())
        
        duration = time.time() - start_time
        
        attacker_wins = sum(1 for r in results if r.get("episode_result", {}).get("attacker_won", False))
        defender_wins = len(results) - attacker_wins
        
        return {
            "success": True,
            "task_id": task_id,
            "num_episodes": num_episodes,
            "duration_seconds": duration,
            "attacker_wins": attacker_wins,
            "defender_wins": defender_wins,
            "defender_win_rate": defender_wins / len(results) if results else 0,
            "best_defender_id": best_defender.agent_id,
            "best_win_rate": best_defender.wins / max(best_defender.total_games, 1),
            "model_path": model_path
        }
        
    except Exception as e:
        logger.error(f"Training task failed: {e}\n{traceback.format_exc()}")
        
        async def log_error():
            from backend.database import get_db_connection
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        INSERT INTO training_sessions 
                        (session_id, start_time, end_time, num_episodes, status, error_message)
                        VALUES ($1, $2, $3, $4, 'failed', $5)
                    """, task_id, datetime.fromtimestamp(start_time), datetime.now(), num_episodes, str(e))
                finally:
                    await conn.close()
                    break
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(log_error())
        
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="backend.workers.training_tasks.update_production_model",
    max_retries=3
)
def update_production_model(self, model_path: str) -> Dict:
    """
    更新生产环境防御模型
    
    Args:
        model_path: 新模型路径
    
    Returns:
        更新结果
    """
    logger.info(f"Updating production model: {model_path}")
    
    try:
        import torch
        from backend.agents.selfplay import DefenseAgent
        
        production_path = "models/production/defense_active.pt"
        os.makedirs(os.path.dirname(production_path), exist_ok=True)
        
        import shutil
        shutil.copy(model_path, production_path)
        
        model = DefenseAgent(
            agent_id="production",
            state_dim=13,
            action_dim=8
        )
        model.policy.load_state_dict(torch.load(model_path))
        model.policy.eval()
        
        from backend.database import get_db_connection
        
        async def update_db():
            async for conn in get_db_connection():
                try:
                    await conn.execute("""
                        UPDATE model_versions SET is_active = FALSE 
                        WHERE model_type = 'defense'
                    """)
                    
                    await conn.execute("""
                        UPDATE model_versions SET is_active = TRUE 
                        WHERE path = $1
                    """, model_path)
                    
                    await conn.execute("""
                        INSERT INTO production_model_history 
                        (model_path, deployed_at, deployed_by)
                        VALUES ($1, CURRENT_TIMESTAMP, 'celery')
                    """, model_path)
                finally:
                    await conn.close()
                    break
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(update_db())
        
        return {
            "success": True,
            "model_path": model_path,
            "production_path": production_path,
            "deployed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update production model: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="backend.workers.training_tasks.evaluate_model",
    max_retries=2
)
def evaluate_model(self, model_path: str, num_episodes: int = 100) -> Dict:
    """
    评估模型性能
    
    Args:
        model_path: 模型路径
        num_episodes: 评估对局数
    
    Returns:
        评估结果
    """
    logger.info(f"Evaluating model: {model_path}")
    
    try:
        import torch
        from backend.agents.selfplay import (
            DefenseAgent,
            AttackAgent,
            CyberBattleEnv,
            Evaluator,
            EvaluationConfig
        )
        
        env = CyberBattleEnv()
        
        defender = DefenseAgent("eval_defender", 13, 8)
        defender.policy.load_state_dict(torch.load(model_path))
        defender.policy.eval()
        
        attacker = AttackAgent("eval_attacker", 8, 8)
        
        config = EvaluationConfig(n_eval_episodes=num_episodes)
        evaluator = Evaluator(defender, attacker, env, config)
        
        results = evaluator.evaluate_defense(num_episodes)
        
        return {
            "success": True,
            "model_path": model_path,
            "num_episodes": num_episodes,
            "tpr": results["defense"]["tpr"],
            "fpr": results["defense"]["fpr"],
            "f1_score": results["defense"]["f1_score"],
            "service_availability": results["defense"]["service_availability"],
            "avg_latency_ms": results["realtime"]["avg_latency_ms"]
        }
        
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name="backend.workers.training_tasks.schedule_continuous_training",
    max_retries=1
)
def schedule_continuous_training(self, hours: int = 24) -> Dict:
    """
    调度持续训练任务
    
    Args:
        hours: 训练持续小时数
    
    Returns:
        调度结果
    """
    from backend.workers.celery_app import app
    
    task_ids = []
    episodes_per_hour = 100
    
    for hour in range(hours):
        eta = datetime.now() + timedelta(hours=hour)
        result = self_play_training_cycle.apply_async(
            args=[episodes_per_hour],
            eta=eta
        )
        task_ids.append(result.id)
    
    return {
        "success": True,
        "scheduled_hours": hours,
        "episodes_per_hour": episodes_per_hour,
        "task_ids": task_ids
    }
