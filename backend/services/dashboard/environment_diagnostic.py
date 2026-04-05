# -*- coding: utf-8 -*-
"""
仪表盘环境诊断模块 - 提示词1-3
基础环境健康检查、后端服务启动诊断、前端依赖与构建检查
"""
import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
class EnvironmentReport:
    timestamp: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    results: List[CheckResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "summary": {
                "total": self.total_checks,
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "skipped": self.skipped,
                "health_score": round(self.passed / self.total_checks * 100, 2) if self.total_checks > 0 else 0
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
    """基础环境健康检查器 - 提示词1"""

    def __init__(self):
        self.results: List[CheckResult] = []

    async def check_python_version(self) -> CheckResult:
        """检查Python版本"""
        start_time = time.time()
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 10:
            status = CheckStatus.PASS
            message = f"Python版本满足要求: {version_str}"
        else:
            status = CheckStatus.FAIL
            message = f"Python版本过低: {version_str}, 需要 >= 3.10"
        
        return CheckResult(
            name="Python版本",
            status=status,
            message=message,
            details={
                "version": version_str,
                "required": ">=3.10"
            },
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=[] if status == CheckStatus.PASS else ["升级Python到3.10或更高版本"]
        )

    async def check_database(self) -> CheckResult:
        """检查数据库连接"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
        if not db_url:
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "fangdudu")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")
            details["config"] = {
                "host": db_host,
                "port": db_port,
                "database": db_name,
                "user": db_user
            }
        else:
            details["url_configured"] = True
        
        try:
            import asyncpg
            conn_params = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", "fangdudu"),
                "timeout": 5
            }
            
            conn = await asyncpg.connect(**conn_params)
            
            version = await conn.fetchval("SELECT version()")
            details["server_version"] = version[:100] if version else "unknown"
            
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            details["tables_count"] = len(tables)
            
            await conn.close()
            
            status = CheckStatus.PASS
            message = f"数据库连接成功, 共{details['tables_count']}张表"
            
        except ImportError:
            status = CheckStatus.FAIL
            message = "asyncpg模块未安装"
            suggestions = ["pip install asyncpg"]
        except Exception as e:
            status = CheckStatus.FAIL
            message = f"数据库连接失败: {str(e)}"
            details["error"] = str(e)
            suggestions = [
                "检查数据库服务是否启动",
                "验证数据库连接配置是否正确",
                "检查网络连接和防火墙设置"
            ]
        
        return CheckResult(
            name="数据库连接",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_redis(self) -> CheckResult:
        """检查Redis连接"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = os.getenv("REDIS_DB", "0")
        
        details["config"] = {
            "host": redis_host,
            "port": redis_port,
            "db": redis_db
        }
        
        try:
            import redis.asyncio as redis
            
            client = redis.Redis(
                host=redis_host,
                port=int(redis_port),
                db=int(redis_db),
                decode_responses=True
            )
            
            await client.ping()
            
            info = await client.info()
            details["version"] = info.get("redis_version", "unknown")
            details["used_memory"] = info.get("used_memory_human", "unknown")
            
            keys = await client.keys("*")
            details["keys_count"] = len(keys)
            
            await client.close()
            
            status = CheckStatus.PASS
            message = f"Redis连接成功, 版本: {details['version']}, 共{details['keys_count']}个键"
            
        except ImportError:
            status = CheckStatus.WARNING
            message = "redis模块未安装, 缓存功能将不可用"
            suggestions = ["pip install redis"]
        except Exception as e:
            status = CheckStatus.WARNING
            message = f"Redis连接失败: {str(e)}, 缓存功能将不可用"
            details["error"] = str(e)
            suggestions = [
                "检查Redis服务是否启动",
                "验证Redis连接配置是否正确"
            ]
        
        return CheckResult(
            name="Redis连接",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_rabbitmq(self) -> CheckResult:
        """检查RabbitMQ连接"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        details["url_configured"] = bool(os.getenv("RABBITMQ_URL"))
        
        try:
            import aio_pika
            
            connection = await aio_pika.connect_robust(rabbitmq_url, timeout=5)
            
            async with connection:
                channel = await connection.channel()
                queues = await channel.get_queue_names()
                details["queues_count"] = len(queues) if queues else 0
                
            status = CheckStatus.PASS
            message = f"RabbitMQ连接成功, 共{details.get('queues_count', 0)}个队列"
            
        except ImportError:
            status = CheckStatus.SKIP
            message = "aio_pika模块未安装, 跳过RabbitMQ检查"
            suggestions = ["pip install aio-pika (可选)"]
        except Exception as e:
            status = CheckStatus.WARNING
            message = f"RabbitMQ连接失败: {str(e)}, 消息队列功能将不可用"
            details["error"] = str(e)
            suggestions = [
                "检查RabbitMQ服务是否启动",
                "验证RabbitMQ连接配置是否正确"
            ]
        
        return CheckResult(
            name="RabbitMQ连接",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_system_dependencies(self) -> CheckResult:
        """检查系统依赖"""
        start_time = time.time()
        details = {}
        suggestions = []
        missing = []
        
        system = platform.system()
        details["system"] = system
        details["machine"] = platform.machine()
        
        if system == "Linux":
            libs = ["libpq", "libssl", "libffi"]
            for lib in libs:
                try:
                    result = subprocess.run(
                        ["ldconfig", "-p"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if lib in result.stdout:
                        details[f"{lib}_installed"] = True
                    else:
                        details[f"{lib}_installed"] = False
                        missing.append(lib)
                except Exception:
                    details[f"{lib}_check_failed"] = True
        
        if missing:
            status = CheckStatus.WARNING
            message = f"缺少系统依赖: {', '.join(missing)}"
            suggestions = [f"sudo apt-get install lib{lib}-dev" for lib in missing]
        else:
            status = CheckStatus.PASS
            message = "系统依赖检查通过"
        
        return CheckResult(
            name="系统依赖",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_virtual_env(self) -> CheckResult:
        """检查虚拟环境"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        details["in_virtual_env"] = in_venv
        details["python_path"] = sys.executable
        details["prefix"] = sys.prefix
        
        if in_venv:
            status = CheckStatus.PASS
            message = f"虚拟环境已激活: {sys.prefix}"
        else:
            status = CheckStatus.WARNING
            message = "未检测到虚拟环境"
            suggestions = [
                "建议使用虚拟环境: python -m venv venv",
                "激活虚拟环境: source venv/bin/activate (Linux/Mac) 或 venv\\Scripts\\activate (Windows)"
            ]
        
        return CheckResult(
            name="虚拟环境",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_dependencies(self) -> CheckResult:
        """检查Python依赖"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        requirements_path = "requirements.txt"
        
        if not os.path.exists(requirements_path):
            status = CheckStatus.WARNING
            message = "requirements.txt文件不存在"
            return CheckResult(
                name="Python依赖",
                status=status,
                message=message,
                details=details,
                duration_ms=(time.time() - start_time) * 1000,
                suggestions=["创建requirements.txt文件"]
            )
        
        try:
            with open(requirements_path, "r") as f:
                required = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
            installed = {}
            missing = []
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                for pkg in packages:
                    installed[pkg["name"].lower()] = pkg["version"]
            
            for req in required:
                pkg_name = req.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].strip().lower()
                if pkg_name not in installed:
                    missing.append(req)
            
            details["total_required"] = len(required)
            details["total_installed"] = len(installed)
            details["missing_count"] = len(missing)
            details["missing"] = missing[:10]
            
            if missing:
                status = CheckStatus.FAIL
                message = f"缺少{len(missing)}个依赖包"
                suggestions = ["pip install -r requirements.txt"]
            else:
                status = CheckStatus.PASS
                message = f"所有依赖已安装, 共{len(required)}个包"
                
        except Exception as e:
            status = CheckStatus.FAIL
            message = f"依赖检查失败: {str(e)}"
            details["error"] = str(e)
            suggestions = ["手动检查requirements.txt"]
        
        return CheckResult(
            name="Python依赖",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_env_file(self) -> CheckResult:
        """检查配置文件"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        env_path = ".env"
        env_example_path = ".env.example"
        
        details["env_exists"] = os.path.exists(env_path)
        details["env_example_exists"] = os.path.exists(env_example_path)
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET_KEY",
            "DB_HOST",
            "DB_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if value:
                details[var] = "configured"
            else:
                missing_vars.append(var)
                details[var] = "missing"
        
        details["missing_vars"] = missing_vars
        
        if not details["env_exists"]:
            status = CheckStatus.FAIL
            message = ".env文件不存在"
            suggestions = [
                "复制.env.example为.env" if details["env_example_exists"] else "创建.env文件",
                "填写必要的环境变量"
            ]
        elif missing_vars:
            status = CheckStatus.WARNING
            message = f"缺少环境变量: {', '.join(missing_vars)}"
            suggestions = [f"在.env中设置{var}" for var in missing_vars]
        else:
            status = CheckStatus.PASS
            message = "配置文件检查通过"
        
        return CheckResult(
            name="配置文件",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def check_static_files(self) -> CheckResult:
        """检查静态文件"""
        start_time = time.time()
        details = {}
        suggestions = []
        
        static_dirs = ["static", "dist", "build", "public"]
        found_dirs = []
        
        for d in static_dirs:
            if os.path.exists(d):
                found_dirs.append(d)
                files = []
                for root, dirs, filenames in os.walk(d):
                    for f in filenames[:20]:
                        files.append(os.path.join(root, f))
                details[f"{d}_files"] = len(files)
        
        details["found_dirs"] = found_dirs
        
        if found_dirs:
            status = CheckStatus.PASS
            message = f"找到静态文件目录: {', '.join(found_dirs)}"
        else:
            status = CheckStatus.WARNING
            message = "未找到静态文件目录"
            suggestions = ["执行前端构建: npm run build"]
        
        return CheckResult(
            name="静态文件",
            status=status,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000,
            suggestions=suggestions
        )

    async def run_all_checks(self) -> EnvironmentReport:
        """运行所有环境检查"""
        self.results = []
        
        checks = [
            self.check_python_version(),
            self.check_database(),
            self.check_redis(),
            self.check_rabbitmq(),
            self.check_system_dependencies(),
            self.check_virtual_env(),
            self.check_dependencies(),
            self.check_env_file(),
            self.check_static_files(),
        ]
        
        self.results = await asyncio.gather(*checks)
        
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == CheckStatus.SKIP)
        
        return EnvironmentReport(
            timestamp=datetime.utcnow().isoformat(),
            total_checks=len(self.results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
            results=self.results
        )


class BackendStartupDiagnostics:
    """后端服务启动诊断器 - 提示词2"""

    def __init__(self, app_module: str = "backend.main:app"):
        self.app_module = app_module
        self.results: List[Dict[str, Any]] = []

    async def check_module_imports(self) -> Dict[str, Any]:
        """检查模块导入"""
        start_time = time.time()
        result = {
            "name": "模块导入检查",
            "status": "unknown",
            "message": "",
            "details": {},
            "duration_ms": 0
        }
        
        try:
            critical_modules = [
                "fastapi",
                "uvicorn",
                "pydantic",
                "asyncpg",
                "redis",
            ]
            
            failed_imports = []
            for module in critical_modules:
                try:
                    __import__(module)
                    result["details"][module] = "ok"
                except ImportError as e:
                    failed_imports.append(module)
                    result["details"][module] = f"failed: {str(e)}"
            
            if failed_imports:
                result["status"] = "fail"
                result["message"] = f"导入失败: {', '.join(failed_imports)}"
            else:
                result["status"] = "pass"
                result["message"] = "所有关键模块导入成功"
                
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"模块导入检查异常: {str(e)}"
            result["details"]["error"] = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def check_app_creation(self) -> Dict[str, Any]:
        """检查应用创建"""
        start_time = time.time()
        result = {
            "name": "应用创建检查",
            "status": "unknown",
            "message": "",
            "details": {},
            "duration_ms": 0
        }
        
        try:
            parts = self.app_module.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid app module format: {self.app_module}")
            
            module_path, app_name = parts
            module_path = module_path.replace("/", ".").replace(".py", "")
            
            module = __import__(module_path, fromlist=[app_name])
            app = getattr(module, app_name)
            
            if hasattr(app, 'routes'):
                result["details"]["routes_count"] = len(app.routes)
            
            if hasattr(app, 'middleware'):
                result["details"]["middleware_count"] = len(app.user_middleware)
            
            result["status"] = "pass"
            result["message"] = f"应用创建成功: {self.app_module}"
            
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"应用创建失败: {str(e)}"
            result["details"]["error"] = str(e)
            result["details"]["error_type"] = type(e).__name__
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def check_route_conflicts(self) -> Dict[str, Any]:
        """检查路由冲突"""
        start_time = time.time()
        result = {
            "name": "路由冲突检查",
            "status": "unknown",
            "message": "",
            "details": {},
            "duration_ms": 0
        }
        
        try:
            parts = self.app_module.split(":")
            module_path, app_name = parts
            module_path = module_path.replace("/", ".").replace(".py", "")
            
            module = __import__(module_path, fromlist=[app_name])
            app = getattr(module, app_name)
            
            routes = {}
            conflicts = []
            
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    path = route.path
                    methods = route.methods or set()
                    
                    for method in methods:
                        key = f"{method}:{path}"
                        if key in routes:
                            conflicts.append(key)
                        routes[key] = route
            
            result["details"]["total_routes"] = len(routes)
            result["details"]["conflicts"] = conflicts
            
            if conflicts:
                result["status"] = "warning"
                result["message"] = f"发现{len(conflicts)}个路由冲突"
            else:
                result["status"] = "pass"
                result["message"] = "无路由冲突"
                
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"路由检查失败: {str(e)}"
            result["details"]["error"] = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def check_port_availability(self, port: int = 8000) -> Dict[str, Any]:
        """检查端口可用性"""
        start_time = time.time()
        result = {
            "name": "端口可用性检查",
            "status": "unknown",
            "message": "",
            "details": {"port": port},
            "duration_ms": 0
        }
        
        try:
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            
            try:
                sock.bind(("127.0.0.1", port))
                sock.close()
                result["status"] = "pass"
                result["message"] = f"端口 {port} 可用"
            except OSError:
                result["status"] = "warning"
                result["message"] = f"端口 {port} 已被占用"
                result["details"]["available"] = False
                
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"端口检查失败: {str(e)}"
            result["details"]["error"] = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def run_startup_diagnostics(self) -> Dict[str, Any]:
        """运行启动诊断"""
        start_time = time.time()
        
        self.results = await asyncio.gather(
            self.check_module_imports(),
            self.check_app_creation(),
            self.check_route_conflicts(),
            self.check_port_availability()
        )
        
        total_duration = (time.time() - start_time) * 1000
        
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        warnings = sum(1 for r in self.results if r["status"] == "warning")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_duration_ms": total_duration,
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "can_start": failed == 0
            },
            "results": self.results
        }


class FrontendBuildChecker:
    """前端构建检查器 - 提示词3"""

    def __init__(self, frontend_dir: str = "frontend"):
        self.frontend_dir = frontend_dir
        self.results: List[Dict[str, Any]] = []

    async def check_package_json(self) -> Dict[str, Any]:
        """检查package.json"""
        start_time = time.time()
        result = {
            "name": "package.json检查",
            "status": "unknown",
            "message": "",
            "details": {},
            "duration_ms": 0
        }
        
        package_path = os.path.join(self.frontend_dir, "package.json")
        
        if not os.path.exists(package_path):
            result["status"] = "fail"
            result["message"] = "package.json文件不存在"
            result["duration_ms"] = (time.time() - start_time) * 1000
            return result
        
        try:
            with open(package_path, "r", encoding="utf-8") as f:
                package = json.load(f)
            
            result["details"]["name"] = package.get("name", "unknown")
            result["details"]["version"] = package.get("version", "unknown")
            
            dependencies = package.get("dependencies", {})
            dev_dependencies = package.get("dev_dependencies", {})
            
            result["details"]["dependencies_count"] = len(dependencies)
            result["details"]["dev_dependencies_count"] = len(dev_dependencies)
            
            scripts = package.get("scripts", {})
            result["details"]["scripts"] = list(scripts.keys())
            
            result["status"] = "pass"
            result["message"] = f"package.json有效, 依赖: {len(dependencies)}, 开发依赖: {len(dev_dependencies)}"
            
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"package.json解析失败: {str(e)}"
            result["details"]["error"] = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def check_node_modules(self) -> Dict[str, Any]:
        """检查node_modules"""
        start_time = time.time()
        result = {
            "name": "node_modules检查",
            "status": "unknown",
            "message": "",
            "details": {},
            "duration_ms": 0
        }
        
        node_modules_path = os.path.join(self.frontend_dir, "node_modules")
        
        if not os.path.exists(node_modules_path):
            result["status"] = "fail"
            result["message"] = "node_modules目录不存在, 需要运行npm install"
            result["suggestions"] = ["cd frontend && npm install"]
            result["duration_ms"] = (time.time() - start_time) * 1000
            return result
        
        try:
            packages = os.listdir(node_modules_path)
            result["details"]["packages_count"] = len(packages)
            
            critical_packages = ["react", "vue", "axios", "echarts"]
            found = []
            missing = []
            
            for pkg in critical_packages:
                if pkg in packages or f"@{pkg}" in " ".join(packages):
                    found.append(pkg)
                else:
                    missing.append(pkg)
            
            result["details"]["critical_found"] = found
            result["details"]["critical_missing"] = missing
            
            if missing:
                result["status"] = "warning"
                result["message"] = f"缺少关键依赖: {', '.join(missing)}"
            else:
                result["status"] = "pass"
                result["message"] = f"node_modules存在, 共{len(packages)}个包"
                
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"node_modules检查失败: {str(e)}"
            result["details"]["error"] = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def check_build_output(self) -> Dict[str, Any]:
        """检查构建输出"""
        start_time = time.time()
        result = {
            "name": "构建输出检查",
            "status": "unknown",
            "message": "",
            "details": {},
            "duration_ms": 0
        }
        
        build_dirs = ["dist", "build", "out"]
        found_build = None
        
        for d in build_dirs:
            build_path = os.path.join(self.frontend_dir, d)
            if os.path.exists(build_path):
                found_build = build_path
                break
        
        if not found_build:
            result["status"] = "warning"
            result["message"] = "未找到构建输出目录"
            result["suggestions"] = ["运行 npm run build 生成构建产物"]
            result["duration_ms"] = (time.time() - start_time) * 1000
            return result
        
        try:
            files = []
            for root, dirs, filenames in os.walk(found_build):
                for f in filenames:
                    if f.endswith(('.js', '.css', '.html')):
                        files.append(os.path.join(root, f))
            
            result["details"]["build_dir"] = os.path.basename(found_build)
            result["details"]["asset_files"] = len(files)
            
            index_html = os.path.join(found_build, "index.html")
            result["details"]["index_html_exists"] = os.path.exists(index_html)
            
            if files and os.path.exists(index_html):
                result["status"] = "pass"
                result["message"] = f"构建输出有效, 共{len(files)}个资源文件"
            else:
                result["status"] = "warning"
                result["message"] = "构建输出不完整"
                
        except Exception as e:
            result["status"] = "fail"
            result["message"] = f"构建输出检查失败: {str(e)}"
            result["details"]["error"] = str(e)
        
        result["duration_ms"] = (time.time() - start_time) * 1000
        return result

    async def run_frontend_checks(self) -> Dict[str, Any]:
        """运行前端检查"""
        start_time = time.time()
        
        self.results = await asyncio.gather(
            self.check_package_json(),
            self.check_node_modules(),
            self.check_build_output()
        )
        
        total_duration = (time.time() - start_time) * 1000
        
        passed = sum(1 for r in self.results if r["status"] == "pass")
        failed = sum(1 for r in self.results if r["status"] == "fail")
        warnings = sum(1 for r in self.results if r["status"] == "warning")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "frontend_dir": self.frontend_dir,
            "total_duration_ms": total_duration,
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "warnings": warnings
            },
            "results": self.results
        }


async def run_dashboard_environment_check() -> Dict[str, Any]:
    """运行仪表盘环境检查"""
    env_checker = EnvironmentChecker()
    backend_checker = BackendStartupDiagnostics()
    frontend_checker = FrontendBuildChecker()
    
    env_report = await env_checker.run_all_checks()
    backend_report = await backend_checker.run_startup_diagnostics()
    frontend_report = await frontend_checker.run_frontend_checks()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": env_report.to_dict(),
        "backend": backend_report,
        "frontend": frontend_report,
        "overall_health": {
            "environment_score": env_report.passed / env_report.total_checks * 100 if env_report.total_checks > 0 else 0,
            "backend_can_start": backend_report["summary"]["can_start"],
            "frontend_ready": frontend_report["summary"]["passed"] >= 2
        }
    }


def generate_environment_report(report: Dict[str, Any]) -> str:
    """生成环境检查报告"""
    lines = [
        "# 仪表盘环境检查报告",
        f"\n**检查时间**: {report['timestamp']}",
        "\n---\n"
    ]
    
    env = report.get("environment", {})
    summary = env.get("summary", {})
    
    lines.append("## 一、基础环境检查\n")
    lines.append(f"- 总检查项: {summary.get('total', 0)}")
    lines.append(f"- 通过: {summary.get('passed', 0)} ✅")
    lines.append(f"- 失败: {summary.get('failed', 0)} ❌")
    lines.append(f"- 警告: {summary.get('warnings', 0)} ⚠️")
    lines.append(f"- 健康度: {summary.get('health_score', 0):.1f}%\n")
    
    for result in env.get("results", []):
        status_icon = {"pass": "✅", "fail": "❌", "warning": "⚠️", "skip": "⏭️"}.get(result["status"], "❓")
        lines.append(f"### {status_icon} {result['name']}")
        lines.append(f"- 状态: {result['status']}")
        lines.append(f"- 消息: {result['message']}")
        if result.get("suggestions"):
            lines.append(f"- 建议: {', '.join(result['suggestions'])}")
        lines.append("")
    
    backend = report.get("backend", {})
    backend_summary = backend.get("summary", {})
    
    lines.append("## 二、后端服务检查\n")
    lines.append(f"- 可启动: {'是' if backend_summary.get('can_start') else '否'}")
    lines.append(f"- 通过: {backend_summary.get('passed', 0)}")
    lines.append(f"- 失败: {backend_summary.get('failed', 0)}\n")
    
    for result in backend.get("results", []):
        status_icon = {"pass": "✅", "fail": "❌", "warning": "⚠️"}.get(result["status"], "❓")
        lines.append(f"- {status_icon} {result['name']}: {result['message']}")
    
    frontend = report.get("frontend", {})
    frontend_summary = frontend.get("summary", {})
    
    lines.append("\n## 三、前端构建检查\n")
    lines.append(f"- 通过: {frontend_summary.get('passed', 0)}")
    lines.append(f"- 失败: {frontend_summary.get('failed', 0)}")
    lines.append(f"- 警告: {frontend_summary.get('warnings', 0)}\n")
    
    for result in frontend.get("results", []):
        status_icon = {"pass": "✅", "fail": "❌", "warning": "⚠️"}.get(result["status"], "❓")
        lines.append(f"- {status_icon} {result['name']}: {result['message']}")
    
    overall = report.get("overall_health", {})
    lines.append("\n## 四、总体评估\n")
    lines.append(f"- 环境健康度: {overall.get('environment_score', 0):.1f}%")
    lines.append(f"- 后端可启动: {'是' if overall.get('backend_can_start') else '否'}")
    lines.append(f"- 前端就绪: {'是' if overall.get('frontend_ready') else '否'}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("仪表盘环境诊断")
        print("=" * 60)
        
        report = await run_dashboard_environment_check()
        print(generate_environment_report(report))
    
    asyncio.run(main())
