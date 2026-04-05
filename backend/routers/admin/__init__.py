"""
管理后台路由模块
"""
from fastapi import APIRouter

router = APIRouter()

from . import users
from . import settings
from . import stats
from . import audit
from . import map
from . import locations
from . import announcements
from . import audit_v2
from . import audit_archives
from . import alerts
from . import audit_report
from . import mascot
from . import logs
from . import alerts_v2
from . import monitor
from . import security
from . import compliance
from . import feedback
from . import reports

router.include_router(users.router, tags=["admin-users"])
router.include_router(settings.router, tags=["admin-settings"])
router.include_router(stats.router, tags=["admin-stats"])
router.include_router(audit.router, tags=["admin-audit"])
router.include_router(map.router, tags=["admin-map"])
router.include_router(locations.router, tags=["admin-locations"])
router.include_router(announcements.router, tags=["admin-announcements"])
router.include_router(audit_v2.router, tags=["admin-audit-v2"])
router.include_router(audit_archives.router, tags=["admin-audit-archives"])
router.include_router(alerts.router, tags=["admin-alerts"])
router.include_router(audit_report.router, tags=["admin-audit-report"])
router.include_router(mascot.router, tags=["admin-mascot"])
router.include_router(logs.router, tags=["admin-logs"])
router.include_router(alerts_v2.router, tags=["admin-alerts-v2"])
router.include_router(monitor.router, tags=["admin-monitor"])
router.include_router(security.router, tags=["admin-security"])
router.include_router(compliance.router, tags=["admin-compliance"])
router.include_router(feedback.router, tags=["admin-feedback"])
router.include_router(reports.router, tags=["admin-reports"])
