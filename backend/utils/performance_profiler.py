"""
性能分析工具
用于定期性能分析和优化建议生成
"""
import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import functools
import cProfile
import pstats
import io
from collections import defaultdict


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    threshold: Optional[float] = None
    status: str = "normal"


@dataclass
class PerformanceReport:
    """性能报告"""
    timestamp: str
    metrics: List[PerformanceMetric]
    recommendations: List[str]
    bottlenecks: List[Dict[str, Any]]
    trends: Dict[str, Any]


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics_history: Dict[str, List[float]] = defaultdict(list)
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.slow_functions: List[Dict[str, Any]] = []
        self.profiler = cProfile.Profile()
        
    def start_profiling(self):
        """开始性能分析"""
        self.profiler.enable()
        print("🔍 性能分析已启动")
        
    def stop_profiling(self) -> Dict[str, Any]:
        """停止性能分析并返回结果"""
        self.profiler.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        
        stats_output = s.getvalue()
        
        return {
            "profile_stats": stats_output,
            "timestamp": datetime.now().isoformat()
        }
    
    def record_metric(self, name: str, value: float, unit: str = "ms", threshold: Optional[float] = None):
        """记录性能指标"""
        self.metrics_history[name].append(value)
        
        if len(self.metrics_history[name]) > 1000:
            self.metrics_history[name] = self.metrics_history[name][-1000:]
        
        status = "normal"
        if threshold and value > threshold:
            status = "warning"
        if threshold and value > threshold * 1.5:
            status = "critical"
        
        return PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            threshold=threshold,
            status=status
        )
    
    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """获取指标统计信息"""
        values = self.metrics_history.get(name, [])
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "p95": sorted(values)[int(len(values) * 0.95)] if values else 0,
            "p99": sorted(values)[int(len(values) * 0.99)] if values else 0,
        }
    
    def analyze_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        trends = {}
        
        for name, values in self.metrics_history.items():
            if len(values) < 10:
                continue
            
            recent = values[-10:]
            earlier = values[-20:-10] if len(values) >= 20 else values[:-10]
            
            if earlier:
                recent_avg = statistics.mean(recent)
                earlier_avg = statistics.mean(earlier)
                
                change_percent = ((recent_avg - earlier_avg) / earlier_avg) * 100 if earlier_avg != 0 else 0
                
                trends[name] = {
                    "trend": "improving" if change_percent < -5 else "degrading" if change_percent > 5 else "stable",
                    "change_percent": round(change_percent, 2),
                    "recent_avg": round(recent_avg, 2),
                    "earlier_avg": round(earlier_avg, 2),
                }
        
        return trends
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        for name, values in self.metrics_history.items():
            stats = self.get_metric_stats(name)
            
            if stats.get("p95", 0) > 1000:
                bottlenecks.append({
                    "metric": name,
                    "type": "high_latency",
                    "p95_ms": stats["p95"],
                    "avg_ms": stats["mean"],
                    "severity": "high" if stats["p95"] > 3000 else "medium"
                })
            
            if stats.get("stdev", 0) > stats.get("mean", 0) * 0.5:
                bottlenecks.append({
                    "metric": name,
                    "type": "high_variance",
                    "stdev_ms": stats["stdev"],
                    "avg_ms": stats["mean"],
                    "severity": "medium"
                })
        
        return bottlenecks
    
    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        bottlenecks = self.identify_bottlenecks()
        trends = self.analyze_trends()
        
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "high_latency":
                recommendations.append(
                    f"⚠️ {bottleneck['metric']} P95延迟 {bottleneck['p95_ms']:.0f}ms 过高，"
                    f"建议优化查询或添加缓存"
                )
            elif bottleneck["type"] == "high_variance":
                recommendations.append(
                    f"📊 {bottleneck['metric']} 响应时间波动较大，"
                    f"建议检查资源竞争或锁等待问题"
                )
        
        for name, trend in trends.items():
            if trend["trend"] == "degrading":
                recommendations.append(
                    f"📉 {name} 性能呈下降趋势（{trend['change_percent']:+.1f}%），"
                    f"建议进行性能调优"
                )
        
        if not recommendations:
            recommendations.append("✅ 系统性能良好，暂无明显优化建议")
        
        return recommendations
    
    def generate_report(self) -> PerformanceReport:
        """生成完整性能报告"""
        metrics = []
        for name in self.metrics_history.keys():
            stats = self.get_metric_stats(name)
            if stats:
                metrics.append(PerformanceMetric(
                    name=name,
                    value=stats["mean"],
                    unit="ms",
                    timestamp=datetime.now().isoformat()
                ))
        
        return PerformanceReport(
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            recommendations=self.generate_recommendations(),
            bottlenecks=self.identify_bottlenecks(),
            trends=self.analyze_trends()
        )
    
    def save_report(self, filename: str = "performance_report.json"):
        """保存性能报告"""
        report = self.generate_report()
        
        report_dict = {
            "timestamp": report.timestamp,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp,
                    "status": m.status
                }
                for m in report.metrics
            ],
            "recommendations": report.recommendations,
            "bottlenecks": report.bottlenecks,
            "trends": report.trends
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"📊 性能报告已保存: {filename}")
        
        return report_dict


def performance_monitor(func: Callable) -> Callable:
    """性能监控装饰器"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            _global_profiler.record_metric(
                name=f"{func.__module__}.{func.__name__}",
                value=duration,
                unit="ms",
                threshold=1000
            )
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            _global_profiler.record_metric(
                name=f"{func.__module__}.{func.__name__}.error",
                value=duration,
                unit="ms"
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            _global_profiler.record_metric(
                name=f"{func.__module__}.{func.__name__}",
                value=duration,
                unit="ms",
                threshold=1000
            )
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            _global_profiler.record_metric(
                name=f"{func.__module__}.{func.__name__}.error",
                value=duration,
                unit="ms"
            )
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


_global_profiler = PerformanceProfiler()


class ContinuousOptimizer:
    """持续优化器"""
    
    def __init__(self, profiler: PerformanceProfiler = None):
        self.profiler = profiler or _global_profiler
        self.optimization_history: List[Dict[str, Any]] = []
        self.scheduled_tasks: List[Dict[str, Any]] = []
        
    async def run_performance_check(self) -> Dict[str, Any]:
        """运行性能检查"""
        print("\n🔍 运行性能检查...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": []
        }
        
        checks = [
            ("数据库查询性能", self._check_database_performance),
            ("API响应时间", self._check_api_response_time),
            ("内存使用情况", self._check_memory_usage),
            ("缓存命中率", self._check_cache_hit_rate),
        ]
        
        for name, check_func in checks:
            try:
                result = await check_func()
                results["checks"].append({
                    "name": name,
                    "status": result["status"],
                    "details": result.get("details", {})
                })
            except Exception as e:
                results["checks"].append({
                    "name": name,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    async def _check_database_performance(self) -> Dict[str, Any]:
        """检查数据库性能"""
        try:
            from ..database import get_db_connection
            
            start_time = time.time()
            conn = await get_db_connection()
            await conn.fetchval("SELECT 1")
            await conn.close()
            duration = (time.time() - start_time) * 1000
            
            self.profiler.record_metric("database.query_time", duration, "ms", 100)
            
            return {
                "status": "healthy" if duration < 100 else "warning",
                "details": {"query_time_ms": round(duration, 2)}
            }
        except Exception as e:
            return {"status": "error", "details": {"error": str(e)}}
    
    async def _check_api_response_time(self) -> Dict[str, Any]:
        """检查API响应时间"""
        stats = self.profiler.get_metric_stats("api.response_time")
        
        if not stats:
            return {"status": "unknown", "details": {"message": "暂无数据"}}
        
        avg_time = stats.get("mean", 0)
        
        return {
            "status": "healthy" if avg_time < 500 else "warning",
            "details": {
                "avg_ms": round(avg_time, 2),
                "p95_ms": round(stats.get("p95", 0), 2)
            }
        }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            self.profiler.record_metric("system.memory_percent", memory.percent, "%", 85)
            
            return {
                "status": "healthy" if memory.percent < 85 else "warning",
                "details": {
                    "percent": round(memory.percent, 1),
                    "used_gb": round(memory.used / 1024**3, 2)
                }
            }
        except Exception as e:
            return {"status": "error", "details": {"error": str(e)}}
    
    async def _check_cache_hit_rate(self) -> Dict[str, Any]:
        """检查缓存命中率"""
        stats = self.profiler.get_metric_stats("cache.hit_rate")
        
        if not stats:
            return {"status": "unknown", "details": {"message": "暂无数据"}}
        
        avg_rate = stats.get("mean", 0)
        
        return {
            "status": "healthy" if avg_rate > 70 else "warning",
            "details": {"hit_rate_percent": round(avg_rate, 1)}
        }
    
    def schedule_optimization(self, task_name: str, interval_hours: int, task_func: Callable):
        """调度优化任务"""
        self.scheduled_tasks.append({
            "name": task_name,
            "interval_hours": interval_hours,
            "func": task_func,
            "last_run": None,
            "next_run": datetime.now()
        })
    
    async def run_scheduled_optimizations(self):
        """运行调度的优化任务"""
        now = datetime.now()
        
        for task in self.scheduled_tasks:
            if task["next_run"] <= now:
                try:
                    print(f"🔧 执行优化任务: {task['name']}")
                    result = await task["func"]()
                    
                    task["last_run"] = now.isoformat()
                    task["next_run"] = now + timedelta(hours=task["interval_hours"])
                    
                    self.optimization_history.append({
                        "task": task["name"],
                        "timestamp": now.isoformat(),
                        "result": result
                    })
                    
                    print(f"✅ 优化任务完成: {task['name']}")
                    
                except Exception as e:
                    print(f"❌ 优化任务失败: {task['name']} - {e}")
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        return {
            "total_optimizations": len(self.optimization_history),
            "recent_optimizations": self.optimization_history[-10:],
            "scheduled_tasks": [
                {
                    "name": t["name"],
                    "interval_hours": t["interval_hours"],
                    "last_run": t["last_run"],
                    "next_run": t["next_run"].isoformat() if t["next_run"] else None
                }
                for t in self.scheduled_tasks
            ]
        }


async def run_continuous_optimization():
    """运行持续优化流程"""
    optimizer = ContinuousOptimizer()
    
    print("=" * 60)
    print("房都督平台 - 持续性能优化")
    print("=" * 60)
    
    results = await optimizer.run_performance_check()
    
    print("\n性能检查结果:")
    for check in results["checks"]:
        status_emoji = "✅" if check["status"] == "healthy" else "⚠️" if check["status"] == "warning" else "❌"
        print(f"  {status_emoji} {check['name']}: {check['status']}")
        if "details" in check:
            for key, value in check["details"].items():
                print(f"      - {key}: {value}")
    
    report = optimizer.profiler.generate_report()
    
    print("\n优化建议:")
    for rec in report.recommendations:
        print(f"  {rec}")
    
    optimizer.profiler.save_report()
    
    return results


if __name__ == "__main__":
    asyncio.run(run_continuous_optimization())
