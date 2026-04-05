# -*- coding: utf-8 -*-
"""
测试与部署模块 - 提示词17-25
E2E测试、压力测试、部署检查、灰度发布
"""
import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import subprocess
import hashlib

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TestSuiteResult:
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_ms: float
    results: List[TestResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class DeploymentCheckItem:
    name: str
    description: str
    passed: bool
    message: str = ""
    critical: bool = True


@dataclass
class DeploymentChecklist:
    items: List[DeploymentCheckItem]
    total_passed: int
    total_failed: int
    all_critical_passed: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class E2ETestRunner:
    """E2E测试运行器 - 提示词17"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._test_results: List[TestResult] = []

    async def run_login_test(self, username: str, password: str) -> TestResult:
        """运行登录测试"""
        start_time = time.time()
        result = TestResult(
            name="admin_login",
            status=TestStatus.PENDING,
            duration_ms=0,
            message="Starting login test"
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/admin/login",
                    json={"username": username, "password": password},
                    timeout=30.0
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    if data.get("access_token"):
                        result.status = TestStatus.PASSED
                        result.message = "Login successful"
                        result.details = {
                            "token_received": True,
                            "user_role": data.get("admin", {}).get("role")
                        }
                    else:
                        result.status = TestStatus.FAILED
                        result.message = "No access token in response"
                elif response.status_code == 401:
                    result.status = TestStatus.FAILED
                    result.message = "Invalid credentials"
                elif response.status_code == 403:
                    result.status = TestStatus.FAILED
                    result.message = "Forbidden - not admin user"
                else:
                    result.status = TestStatus.FAILED
                    result.message = f"Unexpected status code: {response.status_code}"

        except asyncio.TimeoutError:
            result.status = TestStatus.FAILED
            result.message = "Request timeout"
            result.error = "Timeout after 30 seconds"
        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Test error: {str(e)}"
            result.error = str(e)

        self._test_results.append(result)
        return result

    async def run_user_list_test(self, token: str) -> TestResult:
        """运行用户列表测试"""
        start_time = time.time()
        result = TestResult(
            name="user_list",
            status=TestStatus.PENDING,
            duration_ms=0,
            message="Starting user list test"
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/users",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"page": 1, "page_size": 10},
                    timeout=30.0
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    users = data.get("users", [])
                    if isinstance(users, list) and len(users) >= 0:
                        result.status = TestStatus.PASSED
                        result.message = f"Retrieved {len(users)} users"
                        result.details = {"user_count": len(users)}
                    else:
                        result.status = TestStatus.FAILED
                        result.message = "Invalid response structure"
                elif response.status_code == 401:
                    result.status = TestStatus.FAILED
                    result.message = "Unauthorized - invalid token"
                else:
                    result.status = TestStatus.FAILED
                    result.message = f"Unexpected status code: {response.status_code}"

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Test error: {str(e)}"
            result.error = str(e)

        self._test_results.append(result)
        return result

    async def run_agent_status_test(self, token: str) -> TestResult:
        """运行智能体状态测试"""
        start_time = time.time()
        result = TestResult(
            name="agent_status",
            status=TestStatus.PENDING,
            duration_ms=0,
            message="Starting agent status test"
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/agents",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    agents = data.get("agents", data.get("items", []))
                    if isinstance(agents, list):
                        result.status = TestStatus.PASSED
                        result.message = f"Retrieved {len(agents)} agents"
                        result.details = {"agent_count": len(agents)}
                    else:
                        result.status = TestStatus.FAILED
                        result.message = "Invalid response structure"
                else:
                    result.status = TestStatus.FAILED
                    result.message = f"Unexpected status code: {response.status_code}"

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Test error: {str(e)}"
            result.error = str(e)

        self._test_results.append(result)
        return result

    async def run_statistics_test(self, token: str) -> TestResult:
        """运行统计测试"""
        start_time = time.time()
        result = TestResult(
            name="statistics",
            status=TestStatus.PENDING,
            duration_ms=0,
            message="Starting statistics test"
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/admin/statistics",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    if "users" in data or "tasks" in data or "agents" in data:
                        result.status = TestStatus.PASSED
                        result.message = "Statistics retrieved successfully"
                        result.details = data
                    else:
                        result.status = TestStatus.FAILED
                        result.message = "Missing required statistics fields"
                else:
                    result.status = TestStatus.FAILED
                    result.message = f"Unexpected status code: {response.status_code}"

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Test error: {str(e)}"
            result.error = str(e)

        self._test_results.append(result)
        return result

    async def run_config_update_test(self, token: str, key: str, value: str) -> TestResult:
        """运行配置更新测试"""
        start_time = time.time()
        result = TestResult(
            name="config_update",
            status=TestStatus.PENDING,
            duration_ms=0,
            message="Starting config update test"
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/admin/config",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"key": key, "value": value},
                    timeout=30.0
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    if data.get("key") == key:
                        result.status = TestStatus.PASSED
                        result.message = f"Config {key} updated successfully"
                        result.details = data
                    else:
                        result.status = TestStatus.FAILED
                        result.message = "Config update failed"
                elif response.status_code == 401:
                    result.status = TestStatus.FAILED
                    result.message = "Unauthorized"
                else:
                    result.status = TestStatus.FAILED
                    result.message = f"Unexpected status code: {response.status_code}"

        except Exception as e:
            result.status = TestStatus.FAILED
            result.message = f"Test error: {str(e)}"
            result.error = str(e)

        self._test_results.append(result)
        return result

    async def run_all_tests(self, username: str, password: str) -> TestSuiteResult:
        """运行所有E2E测试"""
        start_time = time.time()
        results = []

        login_result = await self.run_login_test(username, password)
        results.append(login_result)

        if login_result.status == TestStatus.PASSED:
            token = login_result.details.get("token_received", "")
            if token:
                results.append(await self.run_user_list_test(token))
                results.append(await self.run_agent_status_test(token))
                results.append(await self.run_statistics_test(token))
                results.append(await self.run_config_update_test(token, "test_key", "test_value"))
            else:
                for i in range(4):
                    results.append(TestResult(
                        name=f"skipped_test_{i}",
                        status=TestStatus.SKIPPED,
                        duration_ms=0,
                        message="Skipped due to login failure"
                    ))

        duration_ms = (time.time() - start_time) * 1000

        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)

        return TestSuiteResult(
            suite_name="admin_e2e_tests",
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=duration_ms,
            results=results
        )


class StressTestRunner:
    """压力测试运行器 - 提示词18"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._results: List[Dict[str, Any]] = []

    async def run_concurrent_test(
        self,
        endpoint: str,
        concurrent_users: int = 50,
        duration_seconds: int = 600,
        requests_per_user: int = 10
    ) -> Dict[str, Any]:
        """运行并发测试"""
        start_time = time.time()
        results = {
            "endpoint": endpoint,
            "concurrent_users": concurrent_users,
            "duration_seconds": duration_seconds,
            "requests_per_user": requests_per_user,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }

        try:
            import httpx
            import asyncio

            async def user_session(user_id: int):
                async with httpx.AsyncClient() as client:
                    login_resp = await client.post(
                        f"{self.base_url}/api/admin/login",
                        json={"username": f"admin{user_id}", "password": "test_password"}
                    )
                    if login_resp.status_code != 200:
                        return None
                    token = login_resp.json().get("access_token")
                    if not token:
                        return None

                    request_times = []
                    for _ in range(requests_per_user):
                        req_start = time.time()
                        try:
                            resp = await client.get(
                                f"{self.base_url}{endpoint}",
                                headers={"Authorization": f"Bearer {token}"},
                                timeout=10.0
                            )
                            req_end = time.time()
                            request_times.append((req_end - req_start) * 1000)
                            if resp.status_code != 200:
                                results["failed_requests"] += 1
                                results["errors"].append({
                                    "user_id": user_id,
                                    "error": f"Status {resp.status_code}"
                                })
                            else:
                                results["successful_requests"] += 1
                        except Exception as e:
                            results["failed_requests"] += 1
                            results["errors"].append({
                                "user_id": user_id,
                                "error": str(e)
                            })
                        results["total_requests"] += requests_per_user
                        return request_times

            await asyncio.gather(
                *[user_session(i) for i in range(concurrent_users)]
            )

            end_time = datetime.utcnow()
            results["end_time"] = end_time.isoformat()
            results["actual_duration_seconds"] = (time.time() - start_time)

            if results["response_times"]:
                all_times = [t for times in results["response_times"] if times for t in times]
                if all_times:
                    results["avg_response_time_ms"] = sum(all_times) / len(all_times)
                    sorted_times = sorted(all_times)
                    results["p95_response_time_ms"] = sorted_times[int(len(sorted_times) * 0.95)]
                    results["min_response_time_ms"] = min(all_times)
                    results["max_response_time_ms"] = max(all_times)
                else:
                    results["avg_response_time_ms"] = 0
                    results["p95_response_time_ms"] = 0
                    results["min_response_time_ms"] = 0
                    results["max_response_time_ms"] = 0

            results["requests_per_second"] = results["total_requests"] / max(results["actual_duration_seconds"], 1)
            results["error_rate"] = (
                results["failed_requests"] / max(results["total_requests"], 1) * 100
                if results["total_requests"] > 0 else 0
            )
            results["success_rate"] = (
                results["successful_requests"] / max(results["total_requests"], 1) * 100
                if results["total_requests"] > 0 else 0
            )

        except Exception as e:
            results["error"] = str(e)

        self._results.append(results)
        return results


class DeploymentChecker:
    """部署检查器 - 提示词22"""

    def __init__(self):
        self._checks: List[DeploymentCheckItem] = []

    async def run_all_checks(self) -> DeploymentChecklist:
        """运行所有部署检查"""
        items = []
        critical_passed = 0
        critical_failed = 0

        for check in self._get_default_checks():
            result = await self._run_check(check)
            items.append(result)
            if result.critical:
                if result.passed:
                    critical_passed += 1
                else:
                    critical_failed += 1

        return DeploymentChecklist(
            items=items,
            total_passed=len([i for i in items if i.passed]),
            total_failed=len([i for i in items if not i.passed]),
            all_critical_passed=critical_failed == 0,
            timestamp=datetime.utcnow().isoformat()
        )

    async def _run_check(self, check: DeploymentCheckItem) -> DeploymentCheckItem:
        """运行单个检查"""
        try:
            if check.name == "unit_tests":
                passed = await self._check_unit_tests()
                return DeploymentCheckItem(
                    name=check.name,
                    description=check.description,
                    passed=passed,
                    message="All unit tests passed" if passed else "Some unit tests failed",
                    critical=check.critical
                )
            elif check.name == "database_connection":
                passed = await self._check_database()
                return DeploymentCheckItem(
                    name=check.name,
                    description=check.description,
                    passed=passed,
                    message="Database connection successful" if passed else "Database connection failed",
                    critical=check.critical
                )
            elif check.name == "redis_connection":
                passed = await self._check_redis()
                return DeploymentCheckItem(
                    name=check.name,
                    description=check.description,
                    passed=passed,
                    message="Redis connection successful" if passed else "Redis connection failed",
                    critical=check.critical
                )
            elif check.name == "environment_variables":
                passed = await self._check_env_vars()
                return DeploymentCheckItem(
                    name=check.name,
                    description=check.description,
                    passed=passed,
                    message="All required env vars set" if passed else "Some env vars missing",
                    critical=check.critical
                )
            elif check.name == "file_permissions":
                passed = await self._check_file_permissions()
                return DeploymentCheckItem(
                    name=check.name,
                    description=check.description,
                    passed=passed,
                    message="All file permissions correct" if passed else "Some file permission issues",
                    critical=check.critical
                )
            else:
                return check
        except Exception as e:
            return DeploymentCheckItem(
                name=check.name,
                description=check.description,
                passed=False,
                message=f"Check error: {str(e)}",
                critical=check.critical
            )

    async def _check_unit_tests(self) -> bool:
        """检查单元测试"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
        return False

    async def _check_database(self) -> bool:
        """检查数据库连接"""
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "fangdudu")
            )
            await conn.close()
            return True
        except Exception:
            return False
        return False

    async def _check_redis(self) -> bool:
        """检查Redis连接"""
        try:
            import redis.asyncio as redis
            client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379"))
            )
            await client.ping()
            await client.close()
            return True
        except Exception:
            return False
        return False

    async def _check_env_vars(self) -> bool:
        """检查环境变量"""
        required_vars = [
            "JWT_SECRET_KEY",
            "DB_HOST",
            "DB_NAME"
        ]
        missing = [v for v in required_vars if not os.getenv(v)]
        return len(missing) == 0

    async def _check_file_permissions(self) -> bool:
        """检查文件权限"""
        critical_paths = [
            "backend/",
            "logs/",
            "data/"
        ]
        for path in critical_paths:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
            if not os.access(path, os.R_OK | os.W_OK):
                return False
        return True

    def _get_default_checks(self) -> List[DeploymentCheckItem]:
        """获取默认检查项"""
        return [
            DeploymentCheckItem(
                name="unit_tests",
                description="All unit tests must pass",
                passed=False,
                message="",
                critical=True
            ),
            DeploymentCheckItem(
                name="database_connection",
                description="Database connection should be available",
                passed=False,
                message="",
                critical=True
            ),
            DeploymentCheckItem(
                name="redis_connection",
                description="Redis connection should be available",
                passed=False,
                message="",
                critical=False
            ),
            DeploymentCheckItem(
                name="environment_variables",
                description="All required environment variables should be set",
                passed=False,
                message="",
                critical=True
            ),
            DeploymentCheckItem(
                name="file_permissions",
                description="Critical directories should be readable and writable",
                passed=False,
                message="",
                critical=False
            ),
        ]


class CanaryDeployment:
    """灰度发布管理器 - 提示词23"""

    def __init__(self, total_users: int = 100):
        self.total_users = total_users
        self._current_percentage: float = 0.0
        self._active_users: set = set()
        self._start_time: datetime = None

    async def start(self, initial_percentage: float = 5.0) -> Dict[str, Any]:
        """开始灰度发布"""
        self._current_percentage = initial_percentage
        self._start_time = datetime.utcnow()
        self._active_users = set()
        return {
            "status": "started",
            "percentage": initial_percentage,
            "start_time": self._start_time.isoformat(),
            "message": f"Canary deployment started with {initial_percentage}% traffic"
        }

    async def update_metrics(self, successful: bool, response_time: float) -> Dict[str, Any]:
        """更新指标"""
        if successful:
            self._current_percentage = min(100.0, self._current_percentage + 5)
        return {
            "current_percentage": self._current_percentage,
            "total_users": self.total_users,
            "active_users": len(self._active_users)
        }

    async def should_rollback(self, error_rate: float = 0.1, response_time_p95: float = 5000) -> bool:
        """判断是否应该回滚"""
        return (
            error_rate > 0.1 or
            response_time_p95 > response_time_p95
        )

    async def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "current_percentage": self._current_percentage,
            "total_users": self.total_users,
            "active_users": len(self._active_users),
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "duration_seconds": (datetime.utcnow() - self._start_time).total_seconds() if self._start_time else 0
        }


class RefactoringReport:
    """重构报告生成器 - 提示词24"""

    def __init__(self):
        self.sections: List[Dict[str, Any]] = []

    def add_section(self, title: str, content: str):
        """添加章节"""
        self.sections.append({
            "title": title,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

    def add_problem(self, description: str, impact: str, solution: str):
        """添加问题"""
        self.add_section(
            f"问题: {description}",
            f"- 影响: {impact}\n- 解决方案: {solution}"
        )

    def add_improvement(self, description: str, before: str, after: str):
        """添加改进"""
        self.add_section(
            f"改进: {description}",
            f"- 之前: {before}\n- 之后: {after}"
        )

    def add_metric(self, name: str, value: Any, unit: str = ""):
        """添加指标"""
        self.add_section(
            f"指标: {name}",
            f"- 值: {value} {unit}"
        )

    def generate_markdown(self) -> str:
        """生成Markdown报告"""
        lines = [
            "# 管理员后台重构报告",
            "",
            f"**生成时间**: {datetime.utcnow().isoformat()}",
            "",
            "---",
            ""
        ]

        for section in self.sections:
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section['content'])
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def save_to_file(self, filepath: str) -> bool:
        """保存到文件"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.generate_markdown())
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False


class TechDocUpdater:
    """技术文档更新器 - 提示词25"""

    def __init__(self):
        self.sections: Dict[str, str] = {}

    def update_api_docs(self, endpoint: str, method: str, description: str, params: Dict, response: Dict):
        """更新API文档"""
        key = f"api_{endpoint}"
        self.sections[key] = f"""
### {method.upper()} {endpoint}

{description}

**请求参数**:
```json
{json.dumps(params, indent=2)}
```

**响应示例**:
```json
{json.dumps(response, indent=2)}
```
"""

    def update_db_schema(self, table: str, columns: List[Dict], description: str):
        """更新数据库文档"""
        key = f"db_{table}"
        self.sections[key] = f"""
### {table}

{description}

**字段**:
"""
        for col in columns:
            self.sections[key] += f"| {col['name']} | {col['type']} | {col.get('description', '')} |\n"
        self.sections[key] += "\n"

    def update_deployment_guide(self, steps: List[str], env_vars: List[str]):
        """更新部署指南"""
        self.sections["deployment"] = f"""
### 部署指南

**部署步骤**:
"""
        for i, step in enumerate(steps, 1):
            self.sections["deployment"] += f"{i}. {step}\n"
        self.sections["deployment"] += "\n"
        self.sections["deployment"] += "**环境变量**:\n"
        for var in env_vars:
            self.sections["deployment"] += f"- `{var}`\n"
        self.sections["deployment"] += "\n"

    def add_faq(self, question: str, answer: str):
        """添加FAQ"""
        if "faq" not in self.sections:
            self.sections["faq"] = "### 常见问题\n\n"
        self.sections["faq"] += f"**Q: {question}**\nA: {answer}\n\n"

    def generate_docs(self) -> Dict[str, str]:
        """生成所有文档"""
        return self.sections

    def save_docs(self, directory: str) -> bool:
        """保存文档到目录"""
        try:
            os.makedirs(directory, exist_ok=True)
            for name, content in self.sections.items():
                filepath = os.path.join(directory, f"{name}.md")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            return True
    except Exception as e:
            logger.error(f"Failed to save docs: {e}")
            return False


e2e_test_runner: Optional[E2ETestRunner] = None
stress_test_runner: Optional[StressTestRunner] = None
deployment_checker: Optional[DeploymentChecker] = None
canary_deployment: Optional[CanaryDeployment] = None
refactoring_report: Optional[RefactoringReport] = None
tech_doc_updater: Optional[TechDocUpdater] = None


async def get_e2e_test_runner(base_url: str = None) -> E2ETestRunner:
    if e2e_test_runner is None:
        e2e_test_runner = E2ETestRunner(base_url)
    return e2e_test_runner


async def get_stress_test_runner(base_url: str = None) -> StressTestRunner:
    if stress_test_runner is None:
        stress_test_runner = StressTestRunner(base_url)
    return stress_test_runner


async def get_deployment_checker() -> DeploymentChecker:
    if deployment_checker is None:
        deployment_checker = DeploymentChecker()
    return deployment_checker


async def get_canary_deployment(total_users: int = 100) -> CanaryDeployment:
    if canary_deployment is None:
        canary_deployment = CanaryDeployment(total_users)
    return canary_deployment


async def get_refactoring_report() -> RefactoringReport:
    if refactoring_report is None:
        refactoring_report = RefactoringReport()
    return refactoring_report


async def get_tech_doc_updater() -> TechDocUpdater:
    if tech_doc_updater is None:
        tech_doc_updater = TechDocUpdater()
    return tech_doc_updater
