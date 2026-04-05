"""
压力测试脚本
使用Locust进行高并发性能测试
"""
import os
import sys
import time
import random
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import statistics

try:
    from locust import HttpUser, task, between, events
    from locust.runners import MasterRunner, WorkerRunner
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    HttpUser = object
    task = lambda f: f
    between = lambda a, b: lambda f: f


@dataclass
class TestScenario:
    name: str
    weight: int = 1
    endpoint: str = "/"
    method: str = "GET"
    payload: Dict[str, Any] = None
    headers: Dict[str, str] = None
    expected_status: int = 200
    min_wait: float = 1.0
    max_wait: float = 3.0


@dataclass
class StressTestConfig:
    host: str = "http://localhost:8000"
    users: int = 100
    spawn_rate: float = 10.0
    run_time: int = 300
    scenarios: List[TestScenario] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.scenarios:
            self.scenarios = self._default_scenarios()
    
    def _default_scenarios(self) -> List[TestScenario]:
        return [
            TestScenario(
                name="health_check",
                weight=1,
                endpoint="/health",
                method="GET"
            ),
            TestScenario(
                name="api_status",
                weight=2,
                endpoint="/api/status",
                method="GET"
            ),
            TestScenario(
                name="user_profile",
                weight=5,
                endpoint="/api/users/me",
                method="GET",
                headers={"Authorization": "Bearer test_token"}
            ),
            TestScenario(
                name="task_list",
                weight=10,
                endpoint="/api/tasks",
                method="GET"
            ),
            TestScenario(
                name="create_task",
                weight=3,
                endpoint="/api/tasks",
                method="POST",
                payload={"title": "Test Task", "description": "Load test task"}
            ),
            TestScenario(
                name="cache_test",
                weight=5,
                endpoint="/api/cache/test",
                method="GET"
            ),
        ]


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[Dict[str, Any]] = []
        self.success_count: int = 0
        self.failure_count: int = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def record_success(self, response_time: float):
        self.response_times.append(response_time)
        self.success_count += 1
    
    def record_failure(self, error: str, endpoint: str):
        self.errors.append({
            "error": error,
            "endpoint": endpoint,
            "timestamp": time.time()
        })
        self.failure_count += 1
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.end_time = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.response_times:
            return {"error": "No data collected"}
        
        total_time = (self.end_time or time.time()) - (self.start_time or 0)
        
        return {
            "total_requests": self.success_count + self.failure_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count) * 100,
            "total_time_seconds": round(total_time, 2),
            "requests_per_second": round((self.success_count + self.failure_count) / max(1, total_time), 2),
            "response_time": {
                "min": round(min(self.response_times), 3),
                "max": round(max(self.response_times), 3),
                "avg": round(statistics.mean(self.response_times), 3),
                "median": round(statistics.median(self.response_times), 3),
                "p95": round(statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times), 3),
                "p99": round(statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times), 3),
            },
            "errors": self.errors[-10:]
        }


if LOCUST_AVAILABLE:
    class FangduLocustUser(HttpUser):
        """房都督平台Locust用户"""
        
        wait_time = between(1, 3)
        
        def on_start(self):
            self.token = f"test_token_{random.randint(1, 10000)}"
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        
        @task(1)
        def health_check(self):
            self.client.get("/health", name="health_check")
        
        @task(2)
        def api_status(self):
            self.client.get("/api/status", name="api_status")
        
        @task(5)
        def get_tasks(self):
            self.client.get(
                "/api/tasks",
                headers=self.headers,
                name="get_tasks"
            )
        
        @task(3)
        def create_task(self):
            payload = {
                "title": f"Load Test Task {random.randint(1, 1000)}",
                "description": "Created during load test",
                "priority": random.choice(["low", "medium", "high"])
            }
            self.client.post(
                "/api/tasks",
                json=payload,
                headers=self.headers,
                name="create_task"
            )
        
        @task(2)
        def get_cache(self):
            self.client.get(
                "/api/cache/stats",
                headers=self.headers,
                name="get_cache_stats"
            )
        
        @task(1)
        def get_metrics(self):
            self.client.get("/metrics", name="get_metrics")


class SimpleLoadTest:
    """简单负载测试（不依赖Locust）"""
    
    def __init__(self, config: StressTestConfig = None):
        self.config = config or StressTestConfig()
        self.metrics = PerformanceMetrics()
        self._running = False
    
    async def _make_request(
        self,
        session,
        scenario: TestScenario
    ) -> float:
        import aiohttp
        
        url = f"{self.config.host}{scenario.endpoint}"
        headers = scenario.headers or {}
        
        start_time = time.time()
        
        try:
            if scenario.method == "GET":
                async with session.get(url, headers=headers) as response:
                    await response.text()
                    elapsed = time.time() - start_time
                    
                    if response.status == scenario.expected_status:
                        self.metrics.record_success(elapsed)
                    else:
                        self.metrics.record_failure(
                            f"Unexpected status: {response.status}",
                            scenario.endpoint
                        )
                    return elapsed
            
            elif scenario.method == "POST":
                async with session.post(
                    url,
                    json=scenario.payload,
                    headers=headers
                ) as response:
                    await response.text()
                    elapsed = time.time() - start_time
                    
                    if response.status == scenario.expected_status:
                        self.metrics.record_success(elapsed)
                    else:
                        self.metrics.record_failure(
                            f"Unexpected status: {response.status}",
                            scenario.endpoint
                        )
                    return elapsed
        
        except Exception as e:
            elapsed = time.time() - start_time
            self.metrics.record_failure(str(e), scenario.endpoint)
            return elapsed
    
    async def _user_session(self, user_id: int):
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            while self._running:
                scenario = random.choices(
                    self.config.scenarios,
                    weights=[s.weight for s in self.config.scenarios]
                )[0]
                
                await self._make_request(session, scenario)
                
                wait_time = random.uniform(
                    scenario.min_wait,
                    scenario.max_wait
                )
                await asyncio.sleep(wait_time)
    
    async def run(self) -> Dict[str, Any]:
        """运行负载测试"""
        import aiohttp
        
        self.metrics.start()
        self._running = True
        
        tasks = []
        for i in range(self.config.users):
            tasks.append(self._user_session(i))
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=self.config.run_time
            )
        except asyncio.TimeoutError:
            pass
        finally:
            self._running = False
            self.metrics.stop()
        
        return self.metrics.get_stats()


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(self, host: str = "http://localhost:8000"):
        self.host = host
        self.results: Dict[str, Any] = {}
    
    async def run_single_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Dict = None,
        iterations: int = 100
    ) -> Dict[str, Any]:
        import aiohttp
        
        times = []
        errors = []
        
        async with aiohttp.ClientSession() as session:
            for _ in range(iterations):
                start = time.time()
                try:
                    if method == "GET":
                        async with session.get(f"{self.host}{endpoint}") as resp:
                            await resp.text()
                            times.append(time.time() - start)
                    elif method == "POST":
                        async with session.post(
                            f"{self.host}{endpoint}",
                            json=payload
                        ) as resp:
                            await resp.text()
                            times.append(time.time() - start)
                except Exception as e:
                    errors.append(str(e))
        
        if not times:
            return {"error": "No successful requests", "errors": errors}
        
        return {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "success_count": len(times),
            "error_count": len(errors),
            "avg_time_ms": round(statistics.mean(times) * 1000, 2),
            "min_time_ms": round(min(times) * 1000, 2),
            "max_time_ms": round(max(times) * 1000, 2),
            "p95_ms": round(statistics.quantiles(times, n=20)[18] * 1000, 2) if len(times) > 20 else round(max(times) * 1000, 2),
        }
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整基准测试"""
        endpoints = [
            ("/health", "GET"),
            ("/api/status", "GET"),
            ("/api/tasks", "GET"),
            ("/api/cache/stats", "GET"),
            ("/metrics", "GET"),
        ]
        
        results = {
            "host": self.host,
            "timestamp": datetime.now().isoformat(),
            "endpoints": {}
        }
        
        for endpoint, method in endpoints:
            result = await self.run_single_endpoint(endpoint, method)
            results["endpoints"][endpoint] = result
        
        all_times = []
        for ep_result in results["endpoints"].values():
            if "avg_time_ms" in ep_result:
                all_times.append(ep_result["avg_time_ms"])
        
        if all_times:
            results["summary"] = {
                "avg_response_time_ms": round(statistics.mean(all_times), 2),
                "max_response_time_ms": round(max(all_times), 2),
                "min_response_time_ms": round(min(all_times), 2),
            }
        
        self.results = results
        return results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        if not self.results:
            return "No results available. Run benchmark first."
        
        lines = [
            "# 房都督平台性能测试报告",
            f"\n**测试时间**: {self.results.get('timestamp', 'N/A')}",
            f"**测试主机**: {self.results.get('host', 'N/A')}",
            "\n## 端点测试结果\n",
            "| 端点 | 方法 | 请求数 | 平均响应(ms) | P95(ms) | 错误数 |",
            "|------|------|--------|-------------|---------|--------|",
        ]
        
        for endpoint, data in self.results.get("endpoints", {}).items():
            lines.append(
                f"| {endpoint} | {data.get('method', 'GET')} | "
                f"{data.get('success_count', 0)} | "
                f"{data.get('avg_time_ms', 'N/A')} | "
                f"{data.get('p95_ms', 'N/A')} | "
                f"{data.get('error_count', 0)} |"
            )
        
        summary = self.results.get("summary", {})
        if summary:
            lines.extend([
                "\n## 总结\n",
                f"- **平均响应时间**: {summary.get('avg_response_time_ms', 'N/A')} ms",
                f"- **最大响应时间**: {summary.get('max_response_time_ms', 'N/A')} ms",
                f"- **最小响应时间**: {summary.get('min_response_time_ms', 'N/A')} ms",
            ])
        
        return "\n".join(lines)


async def run_stress_test(
    host: str = "http://localhost:8000",
    users: int = 50,
    duration: int = 60
) -> Dict[str, Any]:
    """运行压力测试"""
    config = StressTestConfig(
        host=host,
        users=users,
        run_time=duration
    )
    
    tester = SimpleLoadTest(config)
    results = await tester.run()
    
    return results


async def run_benchmark(host: str = "http://localhost:8000") -> str:
    """运行基准测试并生成报告"""
    runner = BenchmarkRunner(host)
    await runner.run_full_benchmark()
    return runner.generate_report()


if __name__ == "__main__":
    async def main():
        print("Running benchmark...")
        report = await run_benchmark()
        print(report)
    
    asyncio.run(main())
