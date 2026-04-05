"""
IP扶持计划 - 定时任务调度器
使用APScheduler管理佣金计算等定时任务
"""
import logging
import os
import sys
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobs.ip_commission_job import run_commission_job, run_with_expiration_check

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def commission_settlement_task():
    logger.info("Running commission settlement task...")
    try:
        result = run_commission_job()
        logger.info(f"Commission settlement result: {result}")
    except Exception as e:
        logger.error(f"Commission settlement task failed: {e}")

def referral_expiration_task():
    logger.info("Running referral expiration task...")
    try:
        expired = run_with_expiration_check()
        logger.info(f"Expired {expired} referrals")
    except Exception as e:
        logger.error(f"Referral expiration task failed: {e}")

def setup_scheduler():
    scheduler.add_job(
        commission_settlement_task,
        CronTrigger(hour=2, minute=0),
        id='commission_settlement',
        name='Commission Settlement Job',
        replace_existing=True
    )
    
    scheduler.add_job(
        referral_expiration_task,
        CronTrigger(hour=3, minute=0),
        id='referral_expiration',
        name='Referral Expiration Job',
        replace_existing=True
    )
    
    logger.info("Scheduler configured with jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: {job.trigger}")

def start_scheduler():
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped")

if __name__ == '__main__':
    logger.info("Starting IP scheduler service...")
    
    start_scheduler()
    
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        stop_scheduler()
        logger.info("Scheduler service stopped")
