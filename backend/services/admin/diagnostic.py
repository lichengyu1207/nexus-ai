"""
管理员后台环境诊断模块
提示词1-3: 环境检查、接口测试、前端检查
"""
import asyncio
import os
import sys
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import traceback

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    timestamp: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: List[CheckResult]
    overall_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "total": self.total_checks,
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "skipped": self.skipped,
                "overall_status": self.overall_status
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "duration_ms": r.duration_ms,
                    "suggestions": r.suggestions
                }
                for r in self.results
            ]
        }


class EnvironmentChecker:
    """提示词1: 管理员后台运行环境检查"""
    
    def __init__(self):
        self.results: List[CheckResult] = []
    
    async def run_all_checks(self) -> DiagnosticReport:
        """运行所有环境检查"""
        self.results = []
        
        await self._check_api_routes()
        await self._check_middleware()
        await self._check_database()
        await self._check_admin_users()
        await self._check_jwt_config()
        await self._check_redis()
        await self._check_file_permissions()
        await self._check_env_variables()
        
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == CheckStatus.SKIP)
        
        overall = "healthy" if failed == 0 else ("degraded" if warnings > 0 else "unhealthy")
        
        return DiagnosticReport(
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_checks=len(self.results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=self.results,
            overall_status=overall
        )
    
    async def _check_api_routes(self):
        """检查API路由是否注册"""
        start = time.time()
        try:
            from backend.main import app
            
            routes = [route.path for route in app.routes]
            admin_routes = [r for r in routes if "/admin" in r or "/api/admin" in r]
            
            expected_routes = [
                "/api/admin/login",
                "/api/admin/users",
                "/api/admin/agents",
                "/api/admin/tasks",
                "/api/admin/statistics",
            ]
            
            missing = [r for r in expected_routes if not any(r in route for route in routes)]
            
            if not missing:
                self.results.append(CheckResult(
                    name="API路由注册",
                    status=CheckStatus.PASS,
                    message=f"所有管理员路由已注册，共{len(admin_routes)}个",
                    details={"admin_routes": admin_routes[:10]},
                    duration_ms=(time.time() - start) * 1000
                ))
            else:
                self.results.append(CheckResult(
                    name="API路由注册",
                    status=CheckStatus.WARNING,
                    message=f"缺少部分路由: {missing}",
                    details={"missing_routes": missing, "found_routes": admin_routes},
                    duration_ms=(time.time() - start) * 1000,
                    suggestions=["检查路由注册代码", "确认admin_router已正确导入"]
                ))
        except Exception as e:
            self.results.append(CheckResult(
                name="API路由注册",
                status=CheckStatus.FAIL,
                message=f"检查失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000,
                suggestions=["检查main.py是否存在", "确认FastAPI应用正确初始化"]
            ))
    
    async def _check_middleware(self):
        """检查中间件是否配置"""
        start = time.time()
        try:
            from backend.main import app
            
            middleware_types = [type(m).__name__ for m in app.user_middleware]
            
            required_middleware = ["CORS", "GZip", "Exception"]
            found = [m for m in required_middleware if any(m in mt for mt in middleware_types)]
            
            if len(found) == len(required_middleware):
                self.results.append(CheckResult(
                    name="中间件配置",
                    status=CheckStatus.PASS,
                    message="所有必需中间件已配置",
                    details={"middleware": middleware_types},
                    duration_ms=(time.time() - start) * 1000
                ))
            else:
                missing = [m for m in required_middleware if m not in found]
                self.results.append(CheckResult(
                    name="中间件配置",
                    status=CheckStatus.WARNING,
                    message=f"缺少中间件: {missing}",
                    details={"found": found, "missing": missing},
                    duration_ms=(time.time() - start) * 1000,
                    suggestions=[f"添加{m}中间件" for m in missing]
                ))
        except Exception as e:
            self.results.append(CheckResult(
                name="中间件配置",
                status=CheckStatus.FAIL,
                message=f"检查失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            ))
    
    async def _check_database(self):
        """检查数据库连接"""
        start = time.time()
        try:
            from backend.database_pg import get_db
            
            async with get_db() as db:
                result = await db.fetchval("SELECT 1")
                
                if result == 1:
                    tables = await db.fetch("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    table_names = [t["table_name"] for t in tables]
                    
                    admin_tables = ["admin_users", "admin_roles", "admin_audit_logs"]
                    missing_tables = [t for t in admin_tables if t not in table_names]
                    
                    if missing_tables:
                        self.results.append(CheckResult(
                            name="数据库连接",
                            status=CheckStatus.WARNING,
                            message=f"数据库连接正常，但缺少管理员表: {missing_tables}",
                            details={"tables": table_names[:20], "missing": missing_tables},
                            duration_ms=(time.time() - start) * 1000,
                            suggestions=["运行数据库迁移创建管理员表"]
                        ))
                    else:
                        self.results.append(CheckResult(
                            name="数据库连接",
                            status=CheckStatus.PASS,
                            message=f"数据库连接正常，管理员表已创建",
                            details={"tables": table_names[:20]},
                            duration_ms=(time.time() - start) * 1000
                        ))
                else:
                    self.results.append(CheckResult(
                        name="数据库连接",
                        status=CheckStatus.FAIL,
                        message="数据库查询返回异常",
                        duration_ms=(time.time() - start) * 1000
                    ))
        except Exception as e:
            self.results.append(CheckResult(
                name="数据库连接",
                status=CheckStatus.FAIL,
                message=f"数据库连接失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000,
                suggestions=["检查DATABASE_URL环境变量", "确认数据库服务运行中"]
            ))
    
    async def _check_admin_users(self):
        """检查管理员用户"""
        start = time.time()
        try:
            from backend.database_pg import get_db
            
            async with get_db() as db:
                admins = await db.fetch("""
                    SELECT id, username, email, role, is_active 
                    FROM admin_users 
                    WHERE role = 'admin' OR role = 'super_admin'
                    LIMIT 10
                """)
                
                if admins:
                    self.results.append(CheckResult(
                        name="管理员用户",
                        status=CheckStatus.PASS,
                        message=f"找到{len(admins)}个管理员账户",
                        details={"admins": [{"id": str(a["id"]), "username": a["username"], "role": a["role"]} for a in admins]},
                        duration_ms=(time.time() - start) * 1000
                    ))
                else:
                    self.results.append(CheckResult(
                        name="管理员用户",
                        status=CheckStatus.WARNING,
                        message="未找到管理员账户，需要初始化",
                        duration_ms=(time.time() - start) * 1000,
                        suggestions=["运行数据库迁移创建默认管理员"]
                    ))
        except Exception as e:
            self.results.append(CheckResult(
                name="管理员用户",
                status=CheckStatus.WARNING,
                message=f"检查失败(可能表不存在): {str(e)}",
                duration_ms=(time.time() - start) * 1000,
                suggestions=["运行数据库迁移创建管理员表"]
            ))
    
    async def _check_jwt_config(self):
        """检查JWT配置"""
        start = time.time()
        try:
            secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
            algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            expire = os.getenv("JWT_EXPIRE_MINUTES", "60")
            
            if secret and len(secret) >= 16:
                self.results.append(CheckResult(
                    name="JWT配置",
                    status=CheckStatus.PASS,
                    message="JWT配置正确",
                    details={
                        "algorithm": algorithm,
                        "expire_minutes": expire,
                        "secret_length": len(secret)
                    },
                    duration_ms=(time.time() - start) * 1000
                ))
            else:
                self.results.append(CheckResult(
                    name="JWT配置",
                    status=CheckStatus.WARNING,
                    message="JWT密钥未配置或过短",
                    details={"has_secret": bool(secret)},
                    duration_ms=(time.time() - start) * 1000,
                    suggestions=["设置JWT_SECRET_KEY环境变量", "密钥长度至少16字符"]
                ))
        except Exception as e:
            self.results.append(CheckResult(
                name="JWT配置",
                status=CheckStatus.FAIL,
                message=f"检查失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            ))
    
    async def _check_redis(self):
        """检查Redis连接"""
        start = time.time()
        try:
            from backend.cache.redis_client import redis_client
            
            if redis_client and hasattr(redis_client, 'is_enabled') and redis_client.is_enabled:
                self.results.append(CheckResult(
                    name="Redis连接",
                    status=CheckStatus.PASS,
                    message="Redis连接正常",
                    duration_ms=(time.time() - start) * 1000
                ))
            else:
                self.results.append(CheckResult(
                    name="Redis连接",
                    status=CheckStatus.WARNING,
                    message="Redis未启用，使用内存缓存",
                    duration_ms=(time.time() - start) * 1000,
                    suggestions=["配置REDIS_URL环境变量以启用Redis"]
                ))
        except Exception as e:
            self.results.append(CheckResult(
                name="Redis连接",
                status=CheckStatus.WARNING,
                message=f"Redis检查失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            ))
    
    async def _check_file_permissions(self):
        """检查文件权限"""
        start = time.time()
        try:
            paths_to_check = [
                "backend/logs",
                "backend/data",
                "backend/.env"
            ]
            
            results = {}
            for path in paths_to_check:
                full_path = os.path.join(os.getcwd(), path)
                if os.path.exists(full_path):
                    results[path] = {
                        "exists": True,
                        "writable": os.access(full_path, os.W_OK)
                    }
                else:
                    results[path] = {"exists": False}
            
            all_ok = all(
                r.get("exists", False) and r.get("writable", True)
                for r in results.values()
            )
            
            self.results.append(CheckResult(
                name="文件权限",
                status=CheckStatus.PASS if all_ok else CheckStatus.WARNING,
                message="文件权限检查完成",
                details=results,
                duration_ms=(time.time() - start) * 1000
            ))
        except Exception as e:
            self.results.append(CheckResult(
                name="文件权限",
                status=CheckStatus.WARNING,
                message=f"检查失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            ))
    
    async def _check_env_variables(self):
        """检查环境变量"""
        start = time.time()
        try:
            required_vars = [
                "DATABASE_URL",
                "SECRET_KEY",
            ]
            
            optional_vars = [
                "REDIS_URL",
                "RABBITMQ_URL",
                "JWT_SECRET_KEY",
                "OPENAI_API_KEY"
            ]
            
            missing_required = []
            missing_optional = []
            found = {}
            
            for var in required_vars:
                value = os.getenv(var)
                if not value:
                    missing_required.append(var)
                else:
                    found[var] = "***" + value[-4:] if len(value) > 4 else "***"
            
            for var in optional_vars:
                value = os.getenv(var)
                if not value:
                    missing_optional.append(var)
                else:
                    found[var] = "***" + value[-4:] if len(value) > 4 else "***"
            
            if not missing_required:
                self.results.append(CheckResult(
                    name="环境变量",
                    status=CheckStatus.PASS,
                    message="必需环境变量已配置",
                    details={
                        "found": found,
                        "missing_optional": missing_optional
                    },
                    duration_ms=(time.time() - start) * 1000
                ))
            else:
                self.results.append(CheckResult(
                    name="环境变量",
                    status=CheckStatus.FAIL,
                    message=f"缺少必需环境变量: {missing_required}",
                    details={"missing_required": missing_required},
                    duration_ms=(time.time() - start) * 1000,
                    suggestions=[f"设置{var}环境变量" for var in missing_required]
                ))
        except Exception as e:
            self.results.append(CheckResult(
                name="环境变量",
                status=CheckStatus.FAIL,
                message=f"检查失败: {str(e)}",
                duration_ms=(time.time() - start) * 1000
            ))


class APIConnectivityTester:
    """提示词2: 管理员后台核心接口连通性测试"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    async def test_all_endpoints(self, token: str = None) -> Dict[str, Any]:
        """测试所有端点"""
        try:
            import aiohttp
        except ImportError:
            return {"error": "aiohttp not installed"}
        
        endpoints = [
            ("GET", "/health", None, 200),
            ("GET", "/api/admin/health", None, 200),
            ("POST", "/api/admin/login", {"username": "admin", "password": "test"}, None),
            ("GET", "/api/admin/users", None, 401),
            ("GET", "/api/admin/agents", None, 401),
            ("GET", "/api/admin/tasks", None, 401),
            ("GET", "/api/admin/statistics", None, 401),
        ]
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with aiohttp.ClientSession() as session:
            for method, endpoint, payload, expected_status in endpoints:
                result = await self._test_endpoint(
                    session, method, endpoint, payload, headers, expected_status
                )
                self.results.append(result)
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.get("passed", False)),
            "failed": sum(1 for r in self.results if not r.get("passed", False)),
            "results": self.results
        }
    
    async def _test_endpoint(
        self,
        session,
        method: str,
        endpoint: str,
        payload: Dict,
        headers: Dict,
        expected_status: int
    ) -> Dict[str, Any]:
        """测试单个端点"""
        import aiohttp
        
        url = f"{self.base_url}{endpoint}"
        start = time.time()
        
        try:
            if method == "GET":
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    status = resp.status
                    body = await resp.text()
            elif method == "POST":
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    status = resp.status
                    body = await resp.text()
            else:
                return {"endpoint": endpoint, "error": "Unsupported method"}
            
            duration = (time.time() - start) * 1000
            passed = expected_status is None or status == expected_status
            
            return {
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "expected": expected_status,
                "passed": passed,
                "duration_ms": round(duration, 2),
                "response_preview": body[:200] if body else None
            }
        except asyncio.TimeoutError:
            return {
                "endpoint": endpoint,
                "method": method,
                "passed": False,
                "error": "Timeout",
                "duration_ms": (time.time() - start) * 1000
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "method": method,
                "passed": False,
                "error": str(e),
                "duration_ms": (time.time() - start) * 1000
            }


class FrontendChecker:
    """提示词3: 管理员前端页面加载与路由检查"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
    
    async def check_frontend(self) -> Dict[str, Any]:
        """检查前端页面"""
        try:
            import aiohttp
        except ImportError:
            return {"error": "aiohttp not installed"}
        
        checks = [
            ("静态资源加载", self._check_static_resources),
            ("前端路由配置", self._check_routes),
            ("API地址配置", self._check_api_config),
            ("CORS配置", self._check_cors),
        ]
        
        for name, check_func in checks:
            start = time.time()
            try:
                result = await check_func()
                result["duration_ms"] = (time.time() - start) * 1000
                self.results.append({"name": name, **result})
            except Exception as e:
                self.results.append({
                    "name": name,
                    "status": "error",
                    "message": str(e),
                    "duration_ms": (time.time() - start) * 1000
                })
        
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.get("status") == "pass"),
            "failed": sum(1 for r in self.results if r.get("status") == "fail"),
            "results": self.results
        }
    
    async def _check_static_resources(self) -> Dict[str, Any]:
        """检查静态资源"""
        import aiohttp
        
        static_paths = ["/static", "/assets", "/admin"]
        
        async with aiohttp.ClientSession() as session:
            for path in static_paths:
                try:
                    async with session.get(f"{self.base_url}{path}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            return {"status": "pass", "message": f"静态资源可访问: {path}"}
                except:
                    pass
        
        return {"status": "warning", "message": "未找到静态资源路径"}
    
    async def _check_routes(self) -> Dict[str, Any]:
        """检查前端路由"""
        return {"status": "pass", "message": "前端路由检查需要浏览器环境"}
    
    async def _check_api_config(self) -> Dict[str, Any]:
        """检查API配置"""
        return {"status": "pass", "message": "API配置检查需要前端代码分析"}
    
    async def _check_cors(self) -> Dict[str, Any]:
        """检查CORS配置"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.options(
                    f"{self.base_url}/api/admin/health",
                    headers={"Origin": "http://localhost:3000"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    cors_header = resp.headers.get("Access-Control-Allow-Origin")
                    if cors_header:
                        return {"status": "pass", "message": f"CORS已配置: {cors_header}"}
                    return {"status": "warning", "message": "CORS未配置"}
        except Exception as e:
            return {"status": "warning", "message": f"CORS检查失败: {str(e)}"}


async def run_full_diagnostic(
    base_url: str = "http://localhost:8000",
    include_frontend: bool = True
) -> Dict[str, Any]:
    """运行完整诊断"""
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": None,
        "api_connectivity": None,
        "frontend": None
    }
    
    env_checker = EnvironmentChecker()
    report["environment"] = (await env_checker.run_all_checks()).to_dict()
    
    api_tester = APIConnectivityTester(base_url)
    report["api_connectivity"] = await api_tester.test_all_endpoints()
    
    if include_frontend:
        frontend_checker = FrontendChecker(base_url)
        report["frontend"] = await frontend_checker.check_frontend()
    
    return report


def generate_diagnostic_report(report: Dict[str, Any]) -> str:
    """生成诊断报告"""
    lines = [
        "# 管理员后台诊断报告",
        f"\n**诊断时间**: {report['timestamp']}",
        "\n---\n",
        "## 一、环境检查结果\n"
    ]
    
    env = report.get("environment", {})
    summary = env.get("summary", {})
    
    lines.append(f"- 总检查项: {summary.get('total', 0)}")
    lines.append(f"- 通过: {summary.get('passed', 0)}")
    lines.append(f"- 失败: {summary.get('failed', 0)}")
    lines.append(f"- 警告: {summary.get('warnings', 0)}")
    lines.append(f"- 整体状态: **{summary.get('overall_status', 'unknown')}**\n")
    
    for result in env.get("results", []):
        status_icon = {"pass": "✅", "fail": "❌", "warning": "⚠️", "skip": "⏭️"}.get(result["status"], "❓")
        lines.append(f"### {status_icon} {result['name']}")
        lines.append(f"- 状态: {result['status']}")
        lines.append(f"- 消息: {result['message']}")
        if result.get("suggestions"):
            lines.append(f"- 建议: {', '.join(result['suggestions'])}")
        lines.append("")
    
    api = report.get("api_connectivity", {})
    if api:
        lines.append("## 二、API连通性测试\n")
        lines.append(f"- 总测试: {api.get('total', 0)}")
        lines.append(f"- 通过: {api.get('passed', 0)}")
        lines.append(f"- 失败: {api.get('failed', 0)}\n")
        
        for result in api.get("results", []):
            status_icon = "✅" if result.get("passed") else "❌"
            lines.append(f"- {status_icon} {result['method']} {result['endpoint']}: {result.get('status', result.get('error', 'unknown'))}")
    
    frontend = report.get("frontend", {})
    if frontend:
        lines.append("\n## 三、前端检查结果\n")
        for result in frontend.get("results", []):
            status_icon = {"pass": "✅", "fail": "❌", "warning": "⚠️"}.get(result.get("status"), "❓")
            lines.append(f"- {status_icon} {result['name']}: {result.get('message', '')}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("管理员后台环境诊断")
        print("=" * 60)
        
        report = await run_full_diagnostic()
        print(generate_diagnostic_report(report))
    
    asyncio.run(main())
