"""
学习系统API路由
Learning System API Router

提供学习、自适应与认知系统的REST API接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

from ..agents.learning_engine import learning_engine, ModelRegistry
from ..agents.experience_collector import experience_collector
from ..agents.ppo_trainer import PPOTrainer, PPOConfig
from ..agents.reflection_module import reflection_module, ReflectionContext, ReflectionTrigger
from ..agents.performance_monitor import performance_monitor, MetricType, TimeGranularity


router = APIRouter(prefix="/api/learning", tags=["learning"])


class TrainingRequest(BaseModel):
    agent_id: str
    priority: int = 1
    config: Optional[Dict[str, Any]] = None


class ReflectionRequest(BaseModel):
    agent_id: str
    trigger: str = "manual"
    context: Optional[Dict[str, Any]] = None


class RecordTaskRequest(BaseModel):
    agent_id: str
    task_id: str
    task_type: str
    success: bool
    duration: float
    reward: float = 0.0
    user_feedback: Optional[str] = None
    error: Optional[str] = None


class ABTestRequest(BaseModel):
    agent_id: str
    version_a: str
    version_b: str
    traffic_split: float = 0.5


@router.get("/status")
async def get_learning_status():
    """获取学习系统整体状态"""
    try:
        global_status = learning_engine.get_global_status()
        
        agents_status = []
        for agent_id in global_status.get("registered_agents", []):
            agent_status = learning_engine.get_agent_status(agent_id)
            
            analysis = performance_monitor.analyzer.analyze_agent_performance(
                agent_id,
                timedelta(hours=24)
            )
            
            agents_status.append({
                "agent_id": agent_id,
                "health_score": analysis.get("health_score", 0),
                "success_rate": analysis.get("task_metrics", {}).get("success_rate", 0),
                "avg_response_time": analysis.get("response_time_metrics", {}).get("avg", 0),
                "satisfaction_rate": analysis.get("satisfaction_metrics", {}).get("satisfaction_rate", 0),
                "total_tasks": analysis.get("task_metrics", {}).get("total", 0),
                "successful_tasks": analysis.get("task_metrics", {}).get("successful", 0),
                "failed_tasks": analysis.get("task_metrics", {}).get("failed", 0),
                "avg_reward": analysis.get("reward_metrics", {}).get("avg", 0),
                "learning_progress": analysis.get("learning_metrics", {}),
                "recommendations": analysis.get("recommendations", []),
                "anomalies": performance_monitor.analyzer.detect_anomalies(agent_id)
            })
        
        return {
            "engine_running": global_status.get("running", False),
            "agents": agents_status,
            "pending_jobs": global_status.get("pending_jobs", 0),
            "total_jobs": global_status.get("total_jobs", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_id}")
async def get_agent_learning_status(agent_id: str):
    """获取指定智能体的学习状态"""
    try:
        agent_status = learning_engine.get_agent_status(agent_id)
        
        analysis = performance_monitor.analyzer.analyze_agent_performance(
            agent_id,
            timedelta(hours=24)
        )
        
        return {
            "agent_id": agent_id,
            "trainer": agent_status.get("trainer", {}),
            "active_model": agent_status.get("active_model"),
            "model_versions": agent_status.get("model_versions", 0),
            "experience_buffer": agent_status.get("experience_buffer", {}),
            "reflection": agent_status.get("reflection", {}),
            "performance_analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/engine/start")
async def start_learning_engine(background_tasks: BackgroundTasks):
    """启动学习引擎"""
    try:
        await learning_engine.start()
        return {"success": True, "message": "学习引擎已启动"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/engine/stop")
async def stop_learning_engine():
    """停止学习引擎"""
    try:
        await learning_engine.stop()
        return {"success": True, "message": "学习引擎已停止"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train/{agent_id}")
async def trigger_training(agent_id: str, background_tasks: BackgroundTasks):
    """触发指定智能体的训练"""
    try:
        job_id = await learning_engine.trigger_immediate_training(agent_id)
        return {"success": True, "job_id": job_id, "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def get_training_jobs(limit: int = Query(20, ge=1, le=100)):
    """获取训练任务列表"""
    try:
        global_status = learning_engine.get_global_status()
        jobs = global_status.get("recent_jobs", [])[:limit]
        
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_training_job_status(job_id: str):
    """获取训练任务状态"""
    try:
        status = learning_engine.get_training_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reflections/{agent_id}")
async def get_reflections(
    agent_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """获取智能体的反思记录"""
    try:
        summary = reflection_module.get_reflection_summary(agent_id)
        
        return {
            "agent_id": agent_id,
            "reflections": [],
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reflect")
async def trigger_reflection(request: ReflectionRequest):
    """触发反思"""
    try:
        if request.trigger == "scheduled":
            result = await reflection_module.scheduled_reflection(
                request.agent_id,
                timedelta(hours=24)
            )
        else:
            context = ReflectionContext(
                task_id=request.context.get("task_id", "") if request.context else "",
                agent_id=request.agent_id,
                task_type=request.context.get("task_type", "") if request.context else "",
                user_input=request.context.get("user_input", "") if request.context else "",
                agent_response=request.context.get("agent_response", "") if request.context else "",
                intermediate_steps=request.context.get("intermediate_steps", []) if request.context else [],
                tools_used=request.context.get("tools_used", []) if request.context else [],
                task_success=request.context.get("task_success", False) if request.context else False,
                user_feedback=request.context.get("user_feedback") if request.context else None,
                task_duration=request.context.get("task_duration", 0) if request.context else 0,
                error_messages=request.context.get("error_messages", []) if request.context else [],
                memory_retrieved=request.context.get("memory_retrieved", []) if request.context else []
            )
            
            if request.context and not request.context.get("task_success", True):
                result = await reflection_module.reflect_on_failure(context)
            else:
                result = await reflection_module.reflect_on_feedback(context)
        
        return {
            "success": True,
            "reflection_id": result.id,
            "analysis": result.analysis,
            "suggestions": [s.format() for s in result.suggestions],
            "training_samples_count": len(result.training_samples)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{agent_id}")
async def get_model_versions(agent_id: str, limit: int = Query(10, ge=1, le=50)):
    """获取智能体的模型版本列表"""
    try:
        versions = learning_engine.model_registry.list_versions(agent_id, limit)
        
        return {
            "agent_id": agent_id,
            "versions": [v.to_dict() for v in versions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback/{agent_id}")
async def rollback_model(agent_id: str):
    """回滚模型到上一个版本"""
    try:
        previous_version = await learning_engine.rollback_model(agent_id)
        
        if previous_version:
            return {
                "success": True,
                "version": previous_version,
                "message": f"已回滚到版本 {previous_version}"
            }
        else:
            return {
                "success": False,
                "message": "没有可回滚的版本"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test")
async def create_ab_test(request: ABTestRequest):
    """创建A/B测试"""
    try:
        experiment = learning_engine.create_ab_experiment(
            agent_id=request.agent_id,
            version_a=request.version_a,
            version_b=request.version_b,
            traffic_split=request.traffic_split
        )
        
        return {
            "success": True,
            "experiment": experiment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ab-test/{experiment_id}")
async def get_ab_test_stats(experiment_id: str):
    """获取A/B测试统计"""
    try:
        stats = learning_engine.ab_testing.get_experiment_stats(experiment_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="实验不存在")
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ab-test/{experiment_id}/end")
async def end_ab_test(experiment_id: str, winner: Optional[str] = None):
    """结束A/B测试"""
    try:
        result = learning_engine.ab_testing.end_experiment(experiment_id, winner)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-task")
async def record_task_performance(request: RecordTaskRequest):
    """记录任务执行性能"""
    try:
        performance_monitor.record_task(
            agent_id=request.agent_id,
            task_id=request.task_id,
            task_type=request.task_type,
            success=request.success,
            duration=request.duration,
            reward=request.reward,
            user_feedback=request.user_feedback,
            error=request.error
        )
        
        return {"success": True, "message": "任务记录已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{agent_id}")
async def get_agent_metrics(
    agent_id: str,
    metric_type: str = Query("avg_reward"),
    granularity: str = Query("hour"),
    hours: int = Query(24, ge=1, le=168)
):
    """获取智能体指标时间序列"""
    try:
        metric_enum = MetricType(metric_type)
        granularity_enum = TimeGranularity(granularity)
        
        series = performance_monitor.get_time_series(
            agent_id=agent_id,
            metric_type=metric_enum,
            granularity=granularity_enum,
            time_range=timedelta(hours=hours)
        )
        
        return {
            "agent_id": agent_id,
            "metric_type": metric_type,
            "granularity": granularity,
            "series": series
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(
    agent_ids: str = Query(""),
    hours: int = Query(24, ge=1, le=168)
):
    """获取仪表盘数据"""
    try:
        agent_list = [a.strip() for a in agent_ids.split(",") if a.strip()]
        
        if not agent_list:
            global_status = learning_engine.get_global_status()
            agent_list = global_status.get("registered_agents", [])
        
        dashboard = performance_monitor.get_dashboard_data(
            agent_ids=agent_list,
            time_range=timedelta(hours=hours)
        )
        
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def export_performance_report(
    agent_ids: str = Query(""),
    hours: int = Query(24, ge=1, le=720),
    format: str = Query("json")
):
    """导出性能报告"""
    try:
        agent_list = [a.strip() for a in agent_ids.split(",") if a.strip()]
        
        if not agent_list:
            global_status = learning_engine.get_global_status()
            agent_list = global_status.get("registered_agents", [])
        
        report = performance_monitor.export_report(
            agent_ids=agent_list,
            time_range=timedelta(hours=hours),
            format=format
        )
        
        if format == "markdown":
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=report, media_type="text/markdown")
        
        return JSONResponse(content=json.loads(report) if isinstance(report, str) else report)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_agents(
    agent_ids: str = Query(...),
    hours: int = Query(24, ge=1, le=168)
):
    """比较多个智能体"""
    try:
        agent_list = [a.strip() for a in agent_ids.split(",") if a.strip()]
        
        if len(agent_list) < 2:
            raise HTTPException(status_code=400, detail="至少需要两个智能体进行比较")
        
        comparison = performance_monitor.analyzer.compare_agents(
            agent_ids=agent_list,
            time_range=timedelta(hours=hours)
        )
        
        return comparison
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experience-buffer")
async def get_experience_buffer_stats():
    """获取经验缓冲区统计"""
    try:
        stats = experience_collector.get_buffer_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register-agent/{agent_id}")
async def register_agent_for_learning(agent_id: str):
    """注册智能体到学习系统"""
    try:
        learning_engine.register_agent(agent_id)
        return {"success": True, "message": f"智能体 {agent_id} 已注册"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import json
