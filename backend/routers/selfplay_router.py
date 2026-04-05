"""
自博弈对抗训练API路由
Self-Play Adversarial Training API Router

提供训练控制、评估、模型管理等REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import time
import asyncio

from ..agents.selfplay import (
    selfplay_env, selfplay_trainer,
    SelfPlayTrainer, NetworkSecurityEnv, SelfPlayAgent,
    AgentRole, AttackType, DefenseAction, TORCH_AVAILABLE
)

try:
    from ..agents.selfplay import (
        SelfPlayTrainingKernel,
        AdvancedCyberBattleEnv as CyberBattleEnv,
        AdvancedAttackAgent as AttackAgent,
        AdvancedDefenseAgent as DefenseAgent,
        RobustTrainer,
        DeploymentModule,
        Evaluator,
        AdversarialConfig,
        DeploymentConfig,
        EvaluationConfig
    )
except ImportError:
    SelfPlayTrainingKernel = None
    CyberBattleEnv = None
    AttackAgent = None
    DefenseAgent = None
    RobustTrainer = None
    DeploymentModule = None
    Evaluator = None
    AdversarialConfig = None
    DeploymentConfig = None
    EvaluationConfig = None

try:
    import torch
except ImportError:
    torch = None


router = APIRouter(prefix="/api/selfplay", tags=["selfplay"])


class TrainRequest(BaseModel):
    num_episodes: int = 10
    update_interval: int = 10


class EvaluateRequest(BaseModel):
    num_games: int = 10


class SaveModelRequest(BaseModel):
    path: str = "champion_model.pt"


@router.get("/status")
async def get_training_status():
    """获取训练状态"""
    try:
        status = selfplay_trainer.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/environment/info")
async def get_environment_info():
    """获取环境信息"""
    return {
        "state_dim": selfplay_env.get_state_dim(),
        "attacker_action_dim": selfplay_env.get_action_dim(AgentRole.ATTACKER),
        "defender_action_dim": selfplay_env.get_action_dim(AgentRole.DEFENDER),
        "attack_types": [t.value for t in AttackType],
        "defense_actions": [d.value for d in DefenseAction]
    }


@router.post("/train")
async def train_episodes(request: TrainRequest, background_tasks: BackgroundTasks):
    """训练指定回合数"""
    try:
        results = []
        
        for _ in range(request.num_episodes):
            result = selfplay_trainer.train_step(request.update_interval)
            results.append(result["episode_result"])
        
        return {
            "success": True,
            "episodes_completed": len(results),
            "results": results[-5:] if len(results) > 5 else results,
            "total_episodes": selfplay_trainer.total_episodes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_agents(request: EvaluateRequest):
    """评估智能体"""
    try:
        result = selfplay_trainer.evaluate(request.num_games)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/population")
async def get_population_status():
    """获取种群状态"""
    return {
        "attacker_population": [a.get_status() for a in selfplay_trainer.attacker_population],
        "defender_population": [a.get_status() for a in selfplay_trainer.defender_population],
        "population_size": selfplay_trainer.population_size
    }


@router.get("/population/attacker/{agent_id}")
async def get_attacker_status(agent_id: str):
    """获取攻击者状态"""
    for agent in selfplay_trainer.attacker_population:
        if agent.agent_id == agent_id:
            return agent.get_status()
    raise HTTPException(status_code=404, detail=f"Attacker {agent_id} not found")


@router.get("/population/defender/{agent_id}")
async def get_defender_status(agent_id: str):
    """获取防御者状态"""
    for agent in selfplay_trainer.defender_population:
        if agent.agent_id == agent_id:
            return agent.get_status()
    raise HTTPException(status_code=404, detail=f"Defender {agent_id} not found")


@router.post("/save-champion")
async def save_champion_model(request: SaveModelRequest):
    """保存冠军模型"""
    try:
        selfplay_trainer.save_champion(request.path)
        return {
            "success": True,
            "path": request.path,
            "champion_id": selfplay_trainer.champion.agent_id if selfplay_trainer.champion else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_training_history(limit: int = Query(100, ge=1, le=1000)):
    """获取训练历史"""
    return {
        "history": selfplay_trainer.training_history[-limit:],
        "total": len(selfplay_trainer.training_history)
    }


@router.get("/statistics")
async def get_training_statistics(days: int = Query(7, ge=1, le=30)):
    """获取训练统计"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT stat_date, population_size, total_episodes,
                           best_attacker_id, best_attacker_win_rate,
                           best_defender_id, best_defender_win_rate,
                           avg_attacker_reward, avg_defender_reward
                    FROM selfplay_population_stats
                    WHERE stat_date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY stat_date DESC
                """ % days)
                
                stats = [dict(row) for row in rows]
                
                return {
                    "statistics": stats,
                    "days": days
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodes")
async def get_episode_history(
    limit: int = Query(50, ge=1, le=200),
    attacker_id: Optional[str] = None,
    defender_id: Optional[str] = None
):
    """获取对战记录"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                query = """
                    SELECT episode_id, attacker_id, defender_id,
                           attacker_reward, defender_reward,
                           attacker_won, steps, created_at
                    FROM selfplay_episodes
                    WHERE 1=1
                """
                params = []
                
                if attacker_id:
                    query += " AND attacker_id = $1"
                    params.append(attacker_id)
                
                if defender_id:
                    query += f" AND defender_id = ${len(params) + 1}"
                    params.append(defender_id)
                
                query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                episodes = [dict(row) for row in rows]
                
                return {
                    "episodes": episodes,
                    "total": len(episodes)
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluations")
async def get_evaluation_history(limit: int = Query(20, ge=1, le=100)):
    """获取评估历史"""
    try:
        from ..database import get_db_connection
        
        async for conn in get_db_connection():
            try:
                rows = await conn.fetch("""
                    SELECT evaluation_id, attacker_id, defender_id,
                           num_games, attacker_wins, defender_wins,
                           attacker_win_rate, defender_win_rate,
                           avg_attacker_reward, avg_defender_reward,
                           created_at
                    FROM selfplay_evaluations
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
                
                evaluations = [dict(row) for row in rows]
                
                return {
                    "evaluations": evaluations,
                    "total": len(evaluations)
                }
            finally:
                await conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_training():
    """重置训练"""
    try:
        global selfplay_trainer
        selfplay_trainer = SelfPlayTrainer(selfplay_env)
        
        return {
            "success": True,
            "message": "训练已重置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles")
async def get_agent_roles():
    """获取智能体角色列表"""
    return {
        "roles": [role.value for role in AgentRole]
    }


@router.get("/attack-types")
async def get_attack_types():
    """获取攻击类型列表"""
    return {
        "types": [{"value": t.value, "name": t.name} for t in AttackType]
    }


@router.get("/defense-actions")
async def get_defense_actions():
    """获取防御动作列表"""
    return {
        "actions": [{"value": d.value, "name": d.name} for d in DefenseAction]
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "total_episodes": selfplay_trainer.total_episodes,
        "population_size": selfplay_trainer.population_size
    }


advanced_env = CyberBattleEnv() if CyberBattleEnv else None
advanced_kernel = SelfPlayTrainingKernel(advanced_env) if (SelfPlayTrainingKernel and advanced_env) else None
robust_trainer = None
deployment_module = None
evaluator = None


class AdvancedTrainRequest(BaseModel):
    num_episodes: int = 100
    update_interval: int = 10
    n_attackers: int = 8
    n_defenders: int = 8


class RobustTrainRequest(BaseModel):
    num_episodes: int = 10
    adv_ratio: float = 0.3
    epsilon: float = 0.1


class DeployRequest(BaseModel):
    quantize: bool = True
    export_onnx: bool = True
    export_torchscript: bool = True
    output_dir: str = "models/deployed"


class EvaluateRequest(BaseModel):
    num_episodes: int = 100
    deterministic: bool = True


class InferenceRequest(BaseModel):
    state: List[float]


class BatchInferenceRequest(BaseModel):
    states: List[List[float]]


@router.get("/kernel/status")
async def get_kernel_status():
    """获取高级训练内核状态"""
    try:
        status = advanced_kernel.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kernel/train")
async def train_kernel(request: AdvancedTrainRequest, background_tasks: BackgroundTasks):
    """高级训练内核训练"""
    try:
        results = []
        
        for _ in range(request.num_episodes):
            result = advanced_kernel.train_step(request.update_interval)
            results.append(result)
        
        return {
            "success": True,
            "episodes_completed": len(results),
            "total_episodes": advanced_kernel.total_episodes,
            "last_result": results[-1] if results else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kernel/evaluate")
async def evaluate_kernel(request: EvaluateRequest):
    """评估高级训练内核"""
    try:
        result = advanced_kernel.evaluate(request.num_episodes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kernel/save-champion")
async def save_kernel_champion(request: SaveModelRequest):
    """保存高级训练内核冠军模型"""
    try:
        advanced_kernel.save_champion(request.path)
        return {
            "success": True,
            "path": request.path,
            "has_champion": advanced_kernel.champion is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robust/initialize")
async def initialize_robust_trainer():
    """初始化对抗鲁棒训练器"""
    global robust_trainer
    
    try:
        if advanced_kernel.defender_population:
            defender = advanced_kernel.defender_population[0]
            attacker = advanced_kernel.attacker_population[0]
            
            config = AdversarialConfig()
            robust_trainer = RobustTrainer(defender, attacker, config)
            
            return {
                "success": True,
                "message": "Robust trainer initialized",
                "config": {
                    "epsilon": config.epsilon,
                    "pgd_steps": config.pgd_steps,
                    "wasserstein_radius": config.wasserstein_radius
                }
            }
        else:
            raise HTTPException(status_code=400, detail="No agents available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/robust/train")
async def train_robust(request: RobustTrainRequest):
    """对抗鲁棒训练"""
    global robust_trainer
    
    try:
        if robust_trainer is None:
            raise HTTPException(status_code=400, detail="Robust trainer not initialized")
        
        metrics = robust_trainer.train_step(
            advanced_env,
            n_episodes=request.num_episodes,
            adv_ratio=request.adv_ratio
        )
        
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/robust/evaluate")
async def evaluate_robustness(n_episodes: int = Query(10, ge=1, le=100)):
    """评估鲁棒性"""
    global robust_trainer
    
    try:
        if robust_trainer is None:
            raise HTTPException(status_code=400, detail="Robust trainer not initialized")
        
        results = robust_trainer.evaluate_robustness(advanced_env, n_episodes)
        
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/robust/metrics")
async def get_robust_metrics():
    """获取鲁棒性指标"""
    global robust_trainer
    
    try:
        if robust_trainer is None:
            return {"metrics": None}
        
        metrics = robust_trainer.get_robustness_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/initialize")
async def initialize_deployment():
    """初始化部署模块"""
    global deployment_module
    
    try:
        if advanced_kernel.champion:
            model = advanced_kernel.champion.policy
        elif advanced_kernel.defender_population:
            model = advanced_kernel.defender_population[0].policy
        else:
            raise HTTPException(status_code=400, detail="No model available for deployment")
        
        config = DeploymentConfig()
        deployment_module = DeploymentModule(model, config)
        
        return {
            "success": True,
            "message": "Deployment module initialized",
            "config": {
                "quantization": config.quantization,
                "precision": config.precision,
                "max_latency_ms": config.max_latency_ms
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/export")
async def deploy_model(request: DeployRequest):
    """导出部署模型"""
    global deployment_module
    
    try:
        if deployment_module is None:
            raise HTTPException(status_code=400, detail="Deployment module not initialized")
        
        result = deployment_module.deploy(
            quantize=request.quantize,
            export_onnx=request.export_onnx,
            export_torchscript=request.export_torchscript,
            output_dir=request.output_dir
        )
        
        return {
            "success": True,
            "deployment_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/start")
async def start_inference_service():
    """启动推理服务"""
    global deployment_module
    
    try:
        if deployment_module is None:
            raise HTTPException(status_code=400, detail="Deployment module not initialized")
        
        deployment_module.start_service()
        
        return {
            "success": True,
            "message": "Inference service started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/stop")
async def stop_inference_service():
    """停止推理服务"""
    global deployment_module
    
    try:
        if deployment_module is None:
            raise HTTPException(status_code=400, detail="Deployment module not initialized")
        
        deployment_module.stop_service()
        
        return {
            "success": True,
            "message": "Inference service stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/infer")
async def run_inference(request: InferenceRequest):
    """运行推理"""
    global deployment_module
    
    try:
        if deployment_module is None:
            raise HTTPException(status_code=400, detail="Deployment module not initialized")
        
        import numpy as np
        state = np.array(request.state, dtype=np.float32)
        
        result = await deployment_module.infer(state)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/infer-sync")
async def run_inference_sync(request: InferenceRequest):
    """同步推理"""
    global deployment_module
    
    try:
        if deployment_module is None:
            raise HTTPException(status_code=400, detail="Deployment module not initialized")
        
        import numpy as np
        state = np.array(request.state, dtype=np.float32)
        
        result = deployment_module.infer_sync(state)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy/benchmark")
async def benchmark_deployment(
    n_requests: int = Query(100, ge=10, le=1000)
):
    """基准测试部署"""
    global deployment_module
    
    try:
        if deployment_module is None:
            raise HTTPException(status_code=400, detail="Deployment module not initialized")
        
        result = deployment_module.benchmark(n_requests)
        
        return {
            "success": True,
            "benchmark": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deploy/status")
async def get_deployment_status():
    """获取部署状态"""
    global deployment_module
    
    try:
        if deployment_module is None:
            return {"status": None, "message": "Deployment module not initialized"}
        
        status = deployment_module.get_status()
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluator/initialize")
async def initialize_evaluator():
    """初始化评估器"""
    global evaluator
    
    try:
        if advanced_kernel.defender_population and advanced_kernel.attacker_population:
            defender = advanced_kernel.defender_population[0]
            attacker = advanced_kernel.attacker_population[0]
            
            config = EvaluationConfig()
            evaluator = Evaluator(defender, attacker, advanced_env, config)
            
            return {
                "success": True,
                "message": "Evaluator initialized",
                "config": {
                    "n_eval_episodes": config.n_eval_episodes,
                    "target_tpr": config.target_tpr,
                    "target_fpr": config.target_fpr,
                    "target_latency_ms": config.target_latency_ms
                }
            }
        else:
            raise HTTPException(status_code=400, detail="No agents available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluator/evaluate")
async def run_evaluation(request: EvaluateRequest):
    """运行评估"""
    global evaluator
    
    try:
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Evaluator not initialized")
        
        result = evaluator.evaluate_defense(
            n_episodes=request.num_episodes,
            deterministic=request.deterministic
        )
        
        return {
            "success": True,
            "evaluation": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluator/attack-types")
async def evaluate_by_attack_type(n_episodes: int = Query(20, ge=5, le=50)):
    """按攻击类型评估"""
    global evaluator
    
    try:
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Evaluator not initialized")
        
        result = evaluator.evaluate_by_attack_type(n_episodes)
        
        return {
            "success": True,
            "results": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluator/game-theory")
async def evaluate_game_theory(n_samples: int = Query(100, ge=10, le=500)):
    """博弈论评估"""
    global evaluator
    
    try:
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Evaluator not initialized")
        
        result = evaluator.evaluate_game_theory(n_samples)
        
        return {
            "success": True,
            "game_theory": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluator/targets")
async def check_targets():
    """检查目标达成情况"""
    global evaluator
    
    try:
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Evaluator not initialized")
        
        result = evaluator.check_targets()
        
        return {
            "success": True,
            "targets": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluator/report")
async def generate_report():
    """生成评估报告"""
    global evaluator
    
    try:
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Evaluator not initialized")
        
        report = evaluator.generate_report()
        
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluator/save-best")
async def save_best_model(request: SaveModelRequest):
    """保存最佳模型"""
    global evaluator
    
    try:
        if evaluator is None:
            raise HTTPException(status_code=400, detail="Evaluator not initialized")
        
        saved = evaluator.save_best_model(request.path)
        
        return {
            "success": saved,
            "path": request.path,
            "best_tpr": evaluator.best_tpr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluator/status")
async def get_evaluator_status():
    """获取评估器状态"""
    global evaluator
    
    try:
        if evaluator is None:
            return {"status": None, "message": "Evaluator not initialized"}
        
        status = evaluator.get_status()
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
