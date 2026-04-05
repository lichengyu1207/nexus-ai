"""
房都督AI - 主入口
FastAPI应用配置和路由注册
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# 加载 .env 文件
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key and not os.getenv(key):
                    os.environ[key] = value

from backend.database import init_db
from backend.utils.settings import load_settings_cache
from backend.routers import analyze, sse, auth, tasks, teams, reports, comments, notifications, public, users, search, export, audit, admin, district_info, parse, disambiguate, feedback, ab_tests, knowledge_base, user_feedback, announcements, performance, preview, seo_landing, events, ip_detection, articles, ip_plan, ip_tools, compare, report_export, atmosphere
from backend.routers import metrics
from backend.routers import onboarding
from backend.routers import integral
from backend.routers import user_source
from backend.routers import plans
from backend.routers import orders
from backend.routers import recharge
from backend.routers import health
from backend.routers import consult
from backend.routers import dialogue
from backend.routers import parallel_consult
from backend.routers import token
from backend.routers import complaints
from backend.routers import uploads
from backend.routers import habit
from backend.routers import core_habits
from backend.routers import admin_recharge
from backend.routers import ip_public
from backend.routers import signin
from backend.routers import integral_logs
from backend.routers import ip_partner
from backend.routers import admin_ip
from backend.routers import points
from backend.routers import enhanced_houses
from backend.routers.admin import feedback as admin_feedback
from backend.routers.admin import reports as admin_reports
from backend.routers.admin import stats as admin_stats
from backend.routers.admin import compliance as admin_compliance
from backend.routers.admin import users as admin_users
from backend.routers.admin import settings as admin_settings
from backend.routers.admin import audit as admin_audit
from backend.routers.admin import map as admin_map
from backend.routers.admin import locations as admin_locations
from backend.routers.admin import announcements as admin_announcements
from backend.routers.admin import audit_v2 as admin_audit_v2
from backend.routers.admin import audit_archives as admin_audit_archives
from backend.routers.admin import alerts as admin_alerts
from backend.routers.admin import audit_report as admin_audit_report
from backend.routers.admin import mascot as admin_mascot
from backend.routers.admin import logs as admin_logs
from backend.routers.admin import alerts_v2 as admin_alerts_v2
from backend.routers.admin import monitor as admin_monitor
from backend.routers.admin import security as admin_security
from backend.routers.admin import integral as admin_integral
from backend.routers.admin import mascot_mgmt as admin_mascot_mgmt
from backend.routers.admin import source_stats as admin_source_stats
from backend.routers.admin import dashboard as admin_dashboard
from backend.routers import evolution_router
from backend.routers import living_router
from backend.routers import ecosystem_router
from backend.routers import counterstrike_router
from backend.routers import business_agents_router
from backend.routers import data_engine_router
from backend.routers import ai_safety_router
from backend.routers import fullchain_router
from backend.routers import ministry_router
from backend.routers import memory_router
from backend.routers import three_provinces_router
from backend.routers import attack_defense_router
from backend.routers import memory_immunity_router
from backend.routers import non_repudiation_router
from backend.routers import batch_tasks
from backend.routers import ws_batch
from backend.routers.admin import audit_simple as admin_audit_simple
from backend.routers.admin import tasks as admin_tasks
from backend.routers.admin import knowledge as admin_knowledge
from backend.routers.admin import data_collection
from backend.routers.admin import geo_tree
from backend.routers import city_stats
from backend.routers.admin import consistency
from backend.routers import privacy
from backend.routers.admin import privacy as admin_privacy
from backend.routers import admin_risk
from backend.logger import setup_logging, get_logger
from backend.exceptions import ExceptionMiddleware, setup_exception_handlers
from backend.middleware.audit import AuditMiddleware
from backend.middleware.performance import PerformanceMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.middleware.language import LanguageMiddleware
from backend.cache.redis_client import init_redis, close_redis
from backend.tasks.task_queue import setup_task_queue, shutdown_task_queue
from backend.monitoring.prometheus import setup_prometheus

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "./logs")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

setup_logging(
    log_level=LOG_LEVEL,
    log_dir=LOG_DIR,
    enable_file_logging=True,
    enable_json_logging=False,
)

logger = get_logger("main")

os.makedirs("uploads/avatars", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Application starting up...")
    
    try:
        await init_db()
        logger.info("Database initialized successfully")
        
        await load_settings_cache()
        logger.info("Settings cache loaded")
        
        from backend.routers.district_info import init_district_info_data
        await init_district_info_data()
        logger.info("District info data initialized")
        
        from backend.tasks.audit_signer import setup_audit_signer
        await setup_audit_signer()
        logger.info("Audit signer started")
        
        from backend.tasks.archive_audit_logs import setup_archive_scheduler
        await setup_archive_scheduler()
        logger.info("Audit archive scheduler started")
        
        from backend.services.anomaly_detector import setup_anomaly_detector
        await setup_anomaly_detector()
        logger.info("Anomaly detector started")
        
        from backend.tasks.token_rollback import setup_token_rollback_scheduler
        await setup_token_rollback_scheduler()
        logger.info("Token rollback scheduler started")
        
        from backend.services.task_queue import get_task_queue
        analysis_task_queue = await get_task_queue()
        analysis_task_queue.start()
        logger.info("Task queue started")
        
        from backend.routers.tasks import register_task_handlers
        await register_task_handlers()
        logger.info("Task handlers registered")
        
        from backend.services.progress_manager import progress_manager
        from backend.sse_manager import sse_manager
        progress_manager.set_sse_manager(sse_manager)
        logger.info("Progress manager initialized")
        
        from backend.tasks.habit_scheduler import setup_habit_scheduler, init_default_tasks
        from backend.tasks.core_habits_scheduler import setup_core_habits_scheduler
        from backend.tasks.recharge_scheduler import setup_recharge_scheduler
        from backend.memory.scheduler import start_memory_scheduler
        from backend.tasks.salary_scheduler import setup_salary_scheduler
        from backend.tasks.auto_work_scheduler import setup_auto_work_scheduler
        from backend.tasks.analysis_task_scheduler import setup_analysis_task_scheduler
        
        await init_default_tasks()
        setup_habit_scheduler()
        setup_core_habits_scheduler()
        setup_recharge_scheduler()
        await start_memory_scheduler()
        setup_salary_scheduler()
        setup_auto_work_scheduler()
        setup_analysis_task_scheduler()
        logger.info("Habit scheduler started")
        logger.info("Memory scheduler started")
        logger.info("Salary scheduler started")
        logger.info("Auto work scheduler started")
        logger.info("Analysis task scheduler started")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    from backend.services.task_queue import task_queue as analysis_task_queue
    analysis_task_queue.stop()
    logger.info("Task queue stopped")
    
    from backend.services.anomaly_detector import shutdown_anomaly_detector
    await shutdown_anomaly_detector()
    logger.info("Anomaly detector stopped")
    
    from backend.tasks.token_rollback import shutdown_token_rollback_scheduler
    await shutdown_token_rollback_scheduler()
    logger.info("Token rollback scheduler stopped")
    
    from backend.tasks.archive_audit_logs import shutdown_archive_scheduler
    await shutdown_archive_scheduler()
    logger.info("Audit archive scheduler stopped")
    
    from backend.tasks.audit_signer import shutdown_audit_signer
    await shutdown_audit_signer()
    logger.info("Audit signer stopped")
    
    from backend.tasks.habit_scheduler import shutdown_habit_scheduler
    await shutdown_habit_scheduler()
    logger.info("Habit scheduler stopped")
    
    from backend.tasks.core_habits_scheduler import shutdown_core_habits_scheduler
    from backend.tasks.recharge_scheduler import shutdown_recharge_scheduler
    from backend.memory.scheduler import stop_memory_scheduler
    from backend.tasks.salary_scheduler import shutdown_salary_scheduler
    from backend.tasks.auto_work_scheduler import shutdown_auto_work_scheduler
    
    await shutdown_core_habits_scheduler()
    await shutdown_recharge_scheduler()
    await stop_memory_scheduler()
    await shutdown_salary_scheduler()
    await shutdown_auto_work_scheduler()
    logger.info("Core habits and recharge schedulers stopped")
    logger.info("Memory scheduler stopped")
    logger.info("Salary scheduler stopped")
    logger.info("Auto work scheduler stopped")
    
    logger.info("Application shutting down...")


app = FastAPI(
  title="Governor Fang",
  description="AI-Powered Property Intelligence Platform",
  version="1.0.0",
  lifespan=lifespan,
  docs_url="/docs" if DEBUG else None,
  redoc_url="/redoc" if DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ExceptionMiddleware, debug=DEBUG)
app.add_middleware(AuditMiddleware)
app.add_middleware(LanguageMiddleware)

setup_exception_handlers(app)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(teams.router)
app.include_router(reports.router)
app.include_router(comments.router)
app.include_router(notifications.router)
app.include_router(public.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(export.router)
app.include_router(audit.router)
app.include_router(admin.router)
app.include_router(admin_users.router)
app.include_router(admin_settings.router)
app.include_router(admin_stats.router)
app.include_router(admin_audit.router)
app.include_router(admin_map.router)
app.include_router(admin_locations.router)
app.include_router(analyze.router)
app.include_router(sse.router)
app.include_router(district_info.router)
app.include_router(parse.router)
app.include_router(disambiguate.router)
app.include_router(feedback.router)
app.include_router(events.router)
app.include_router(ip_detection.router)
app.include_router(articles.router)
app.include_router(ip_plan.router)
app.include_router(ip_tools.router)
app.include_router(compare.router)
app.include_router(report_export.router)
app.include_router(metrics.router)
app.include_router(health.router)
app.include_router(onboarding.router)
app.include_router(ab_tests.router)
app.include_router(knowledge_base.router)
app.include_router(user_feedback.router)
app.include_router(admin_feedback.router)
app.include_router(admin_reports.router)
app.include_router(admin_compliance.router)
app.include_router(announcements.router)
app.include_router(admin_announcements.router)
app.include_router(admin_audit_v2.router)
app.include_router(admin_audit_archives.router)
app.include_router(admin_alerts.router)
app.include_router(admin_audit_report.router)
app.include_router(admin_mascot.router)
app.include_router(performance.router)
app.include_router(admin_logs.router)
app.include_router(admin_alerts_v2.router)
app.include_router(admin_monitor.router)
app.include_router(admin_security.router)
app.include_router(admin_integral.router)
app.include_router(admin_mascot_mgmt.router)
app.include_router(admin_source_stats.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_tasks.router)
app.include_router(admin_knowledge.router)
app.include_router(admin_audit_simple.router)
app.include_router(data_collection.router)
app.include_router(evolution_router.router)
app.include_router(memory_immunity_router.router)
app.include_router(non_repudiation_router.router)
app.include_router(living_router.router)
app.include_router(ecosystem_router.router)
app.include_router(counterstrike_router.router)
app.include_router(business_agents_router.router)
app.include_router(data_engine_router.router)
app.include_router(ai_safety_router.router)
app.include_router(fullchain_router.router)
app.include_router(ministry_router.router)
app.include_router(three_provinces_router.router)
app.include_router(memory_router.router)
app.include_router(attack_defense_router.router)
app.include_router(batch_tasks.router)
app.include_router(ws_batch.router)
app.include_router(geo_tree.router)
app.include_router(city_stats.router)
app.include_router(plans.router)
app.include_router(orders.router)
app.include_router(recharge.router)
app.include_router(user_source.router)
app.include_router(integral.router, prefix="/api")
app.include_router(preview.router)
app.include_router(seo_landing.router)
app.include_router(consult.router)
app.include_router(parallel_consult.router)
from backend.routers import public_consult
app.include_router(public_consult.router)
app.include_router(dialogue.router)
app.include_router(token.router)
app.include_router(complaints.router)
app.include_router(uploads.router)
app.include_router(habit.router)
app.include_router(core_habits.router)
app.include_router(admin_recharge.router)
app.include_router(admin_risk.router)
app.include_router(ip_public.router)
app.include_router(ip_partner.router)
app.include_router(admin_ip.router)
app.include_router(signin.router)
app.include_router(points.router)
app.include_router(integral_logs.router)
from backend.routers import enhanced_houses
app.include_router(enhanced_houses.router)
from backend.routers import image_upload
app.include_router(image_upload.router)
from backend.routers import governance
from backend.routers import market
from backend.routers import recruit
from backend.routers import auto_work
from backend.routers import dashboard
app.include_router(governance.router)
app.include_router(market.router)
app.include_router(recruit.router)
app.include_router(auto_work.router)
app.include_router(dashboard.router)
app.include_router(consistency.router)
app.include_router(privacy.router)
app.include_router(admin_privacy.router)
from backend.routers import memory
app.include_router(memory.router, prefix="/api")
from backend.routers import hippocampus
app.include_router(hippocampus.router)
from backend.routers import unified_admin
app.include_router(unified_admin.router)
from backend.routers import enhanced_features
from backend.routers import admin_knowledge as admin_knowledge_router
from backend.routers import learning_router
from backend.routers import dudu_router
from backend.routers import security_router
from backend.routers import selfplay_router
from backend.routers import evolution_router
from backend.routers import agent_dashboard
from backend.routers import cognition as cognition_router
from backend.routers import five_end_router
from backend.api import demo_api
from backend.routers import geo
from backend.routers import monitor
from backend.routers import mingpan_router
from backend.routers import reading_router
from backend.routers import decision_router
from backend.routers import chat_router
from backend.routers import consultation_router
from backend.routers import skill_router
from backend.routers import recruitments

app.include_router(enhanced_features.router)
app.include_router(consultation_router.router)
app.include_router(monitor.router)
app.include_router(mingpan_router.router)
app.include_router(reading_router.router)
app.include_router(decision_router.router)
app.include_router(chat_router.router)
app.include_router(demo_api.router)
app.include_router(agent_dashboard.router)
app.include_router(cognition_router.router)
app.include_router(geo.router)
app.include_router(admin_knowledge_router.router)
app.include_router(learning_router.router)
app.include_router(dudu_router.router)
app.include_router(security_router.router)
app.include_router(selfplay_router.router)
app.include_router(evolution_router.router)
app.include_router(five_end_router.router)
app.include_router(skill_router.router)
app.include_router(recruitments.router)
app.include_router(atmosphere.router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    """Root path"""
    return {
        "name": "Governor Fang",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查 - 返回系统状态"""
    import shutil
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    try:
        from backend.database import get_db_connection
        conn = await get_db_connection()
        await conn.fetchval("SELECT 1")
        await conn.close()
        health_status["components"]["database"] = {"status": "healthy", "type": "postgresql"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)[:100]}
    
    try:
        disk = shutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        health_status["components"]["disk"] = {
            "status": "healthy" if disk_percent < 90 else "warning",
            "used_percent": round(disk_percent, 1),
            "free_gb": round(disk.free / (1024**3), 1)
        }
    except Exception as e:
        health_status["components"]["disk"] = {"status": "unknown", "error": str(e)[:50]}
    
    try:
        data_dir = ROOT_DIR / "data"
        if data_dir.exists():
            db_file = data_dir / "property-ai.db"
            db_size = db_file.stat().st_size / (1024**2) if db_file.exists() else 0
            health_status["components"]["data"] = {
                "status": "healthy",
                "db_size_mb": round(db_size, 1)
            }
    except Exception as e:
        health_status["components"]["data"] = {"status": "unknown", "error": str(e)[:50]}
    
    return health_status


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    import time
    import uuid
    
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    start_time = time.time()
    
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client": request.client.host if request.client else None
        }
    )
    
    try:
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {type(e).__name__}: {str(e)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration * 1000, 2),
                "error": str(e)
            }
        )
        raise
