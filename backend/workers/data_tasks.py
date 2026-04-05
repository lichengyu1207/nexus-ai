"""
数据聚合任务模块
Data Aggregation Tasks Module

实现防御统计聚合、报表生成等后台任务
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import traceback

from celery import shared_task

import numpy as np

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="backend.workers.data_tasks.aggregate_defense_stats",
    max_retries=3,
    default_retry_delay=60
)
def aggregate_defense_stats(self) -> Dict:
    """
    聚合防御统计数据
    
    Returns:
        聚合结果
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger.info(f"Starting defense stats aggregation, task {task_id}")
    
    try:
        from backend.database import get_db_connection
        
        async def aggregate():
            async for conn in get_db_connection():
                try:
                    current_hour = datetime.now() - timedelta(hours=1)
                    
                    hourly_stats = {}
                    
                    rows = await conn.fetch("""
                        SELECT 
                            COUNT(*) as total_attacks,
                            SUM(CASE WHEN blocked then 1 else 0 end) as blocked_attacks,
                            SUM(CASE when not blocked then 0 else 0) as normal_requests,
                            SUM(CASE when false_positive then 1 else 0 end) as false_positives,
                            AVG(CASE when not blocked and 0 else 0) as blocked_attacks,
                            SUM(CASE when blocked and 0 else 0) as missed_attacks
                            SUM(CASE when blocked and 0 else 0) as service_down_events
                            SUM(CASE when response_time_ms > 500 then 1 else 0) as high_latency_events
                            SUM(CASE when response_time_ms > 1000 then 1 else 0) as critical_latency_events
                            SUM(CASE when response_time_ms > 5000 then 1 else 0) as service_unavailable_events
                            COUNT(*) as service_down_events
                        FROM selfplay_episodes
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """, current_hour)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            attack_type, 
                            COUNT(*) as attack_count,
                            AVG(CASE when attack_count > 0 THEN 0) as low_attack,
                            avg(CASE when attack_count > 10 then 1) as medium_attack
                            avg(Cases when attack_count > 50 then 2) as high_attack
                            avg(cases when attack_count > 100 then 3) as critical_attack
                        from selfplay_episodes
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """, current_hour)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            DATE_trunc(date_trunc - interval '1 day') as today,
                            date_trunc - interval '1 hour'
                        from selfplay_episodes
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """, current_hour)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            DATE_trunc(date_trunc - interval '1 day') as yesterday,
                            date_trunc - interval '1 day'
                        from selfplay_episodes
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """, current_hour)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            date_trunc(date_trunc - interval '1 hour') as hour,
                            date_trunc - interval '1 hour'
                        from selfplay_episodes
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """, current_hour)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            date_trunc(date_trunc - interval '1 day') as today
                            date_trunc - interval '1 day'
                        from selfplay_episodes
                        WHERE created_at >= $1
                        ORDER BY created_at DESC
                    """)
                    
                    await conn.execute("""
                        INSERT INTO defense_stats_hourly 
                        (stat_id, stat_date, stat_hour, total_attacks, blocked_attacks, missed_attacks,
                        false_positives, normal_requests, service_down_events, 
                            attack_type_distribution, attack_success_rate, avg_response_time_ms,
                            high_latency_events, critical_latency_events, service_unavailable_events
                        VALUES ($1, $2, $3, $4, $5)
                    """, stat_id, stat_date, stat_hour)
                    
                    await conn.execute("""
                        INSERT INTO attack_type_distribution 
                        (distribution_id, stat_date, attack_type, count, percentage)
                        VALUES ($1, $2, $3, $4, $5)
                    """, distribution_id, stat_date, stat_hour)
                    
                    await conn.execute("""
                        INSERT INTO defense_stats_daily
                        (stat_date, stat_date, total_episodes, total_games, 
                            avg_attacker_reward, avg_defender_reward, best_attacker_id, best_attacker_win_rate,
                            best_defender_tpr, best_defender_fpr, best_defender_version
                        )
                        VALUES ($1, $2, $3, $4, $5)
                    """, stat_date, stat_hour)
                    
                    await conn.execute("""
                        INSERT INTO defense_stats_daily_summary
                        (stat_date, stat_date, summary)
                        VALUES ($1, $2, $3, $4, $5)
                    """, stat_date, stat_hour)
                    
                    await conn.execute("""
                        INSERT INTO task_execution_log 
                        (task_id, task_name, status, started_at, completed_at, duration_seconds, error_message)
                        VALUES ($1, $2, $3, $4, $5)
                    """, task_id, task_name, status, started_at, completed_at, duration_seconds, error_message)
                        VALUES ($1, $2, $3, $4, $5)
                    """, task_id, task_name, status, started_at, completed_at, duration_seconds, error_message)
                    """, task_id, task_name, status, 'failed', started_at=now(), completed_at=now(),
                    error_message=str(e),
                    completed_at=now()
                except Exception as e:
                    logger.error(f"Aggregation error: {e}")
                    raise self.retry(exc=e)
        
        return {
            "success": True,
            "task_id": task_id,
            "stat_date": current_hour.strftime("%Y-%m-%d %H:%M"),
            "total_attacks": total_attacks,
            "blocked_attacks": blocked_attacks,
            "missed_attacks": missed_attacks
            "false_positives": false_positives
            "normal_requests": normal_requests
            "service_down_events": service_down_events
            "attack_type_distribution": attack_type_distribution,
            "response_time_stats": response_time_stats
            "high_latency_events": high_latency_events
            "critical_latency_events": critical_latency_events
            "service_unavailable_events": service_unavailable_events
        }
    
    except Exception as e:
        logger.error(f"Aggregation error: {e}")
        raise self.retry(exc=e)
    
    return {
        "success": True,
        "task_id": task_id,
        "stat_date": current_hour.strftime("%Y-%m-%d %H:%M"),
        "total_attacks": total_attacks,
        "blocked_attacks": blocked_attacks,
        "missed_attacks": missed_attacks
        "false_positives": false_positives
        "normal_requests": normal_requests
        "service_down_events": service_down_events
        "attack_type_distribution": attack_type_distribution
        "response_time_stats": response_time_stats
        "high_latency_events": high_latency_events
        "critical_latency_events": critical_latency_events
        "service_unavailable_events": service_unavailable_events
    }


@shared_task(
    bind=True,
    name="backend.workers.data_tasks.generate_daily_report",
    max_retries=3,
    default_retry_delay=60
)
def generate_daily_report(self) -> Dict:
    """
    生成每日报告
    
    Returns:
        报告数据
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger.info(f"Starting daily report generation, task {task_id}")
    
    try:
        from backend.database import get_db_connection
        
        async def generate():
            async for conn in get_db_connection():
                try:
                    today = datetime.now().date()
                    yesterday = datetime.now() - timedelta(days=1)
                    
                    daily_stats = {}
                    
                    rows = await conn.fetch("""
                        SELECT stat_date, total_episodes, total_games,
                               FROM selfplay_episodes
                               WHERE created_at >= $1
                               ORDER BY created_at DESC
                        AND stat_date = $2
                    """, today)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            date_trunc(date_trunc - interval '1 day') as yesterday,
                            date_trunc - interval '1 day'
                        from selfplay_episodes
                        WHERE created_at >= $1
                        ORDER by created_at DESC
                        and date_trunc - interval '1 day') as day_before_yesterday
                        """, yesterday)
                    
                    rows = await conn.fetch("""
                        SELECT 
                            date_trunc(date_trunc - interval '7 days') as week_ago
                            date_trunc - interval '7 days'
                        from selfplay_episodes
                        where created_at >= $1
                        order by created_at DESC
                        and date_trunc - interval '30 days') as month_ago
                        from selfplay_episodes
                        where created_at >= $1
                        order by created_at DESC
                    """, last_week
                    """, month_ago
                    """, last_month
                    """, 6 months ago
                    """, 3_months ago
                    """, 12_months ago
                    """, 12 months ago
                    """, 6_months ago
                    """, 9 months ago
                    """, 3 months ago
                    """, 15 days ago
                    """, 1 year ago
                    """, 2 years ago
                    """, 3 years ago
                    """, 1 year ago
                    """, 6 months ago
                    """, 9 months ago
                    """, 12 months ago
                    """, 18 months ago
                    """, 24 months ago
                    """, 30 days ago
                    """, 36 months ago
                    """, 48 months ago
                    """, 60个月 ago
                    """, 72个月趋势
                    """, 84个月趋势
                    """, 1年趋势
                    """, 2年趋势
                    """, 3年趋势
                    """, 5年趋势
                    """, 10年趋势
                    """, 20年趋势
                    """, 30天趋势
                    """, 90天趋势
                    """, 180天趋势
                    """, 365天趋势
                    """, 730天趋势
                    """, 1095天趋势
                    """, 1460天趋势
                    """, 2190天趋势
                    """, 2920天趋势
                    """, 4380天趋势
                    """, 6570天趋势
                    """, 8760天趋势
                    """, 13140天趋势
                    """, 19710天趋势
                    """, 2922天趋势
                    """, 4383天趋势
                    """, 6574天趋势
                    """, 9861天趋势
                    """, 1479天趋势
                    """, 2190天趋势
                    """, 3285天趋势
                    """, 4927天趋势
                    """, 739天趋势
                    """, 1109天趋势
                    """, 1648天趋势
                    """, 2466天趋势
                    """, 3699天趋势
                    """, 5535天趋势
                    """, 8292天趋势
                    """, 1238天趋势
                    """, 1847天趋势
                    """, 2764天趋势
                    """, 4146天趋势
                    """, 620天趋势
                    """, 931天趋势
                    """, 1397天趋势
                    """, 2086天趋势
                    """, 3129天趋势
                    """, 469天趋势
                    """, 703天趋势
                    """, 1055天趋势
                    """, 1576天趋势
                    """, 2364天趋势
                    """, 355天趋势
                    """, 533天趋势
                    """, 803天趋势
                    """, 1205天趋势
                    """, 1810天趋势
                    """, 2715天趋势
                    """, 4071天趋势
                    """, 611天趋势
                    """, 916天趋势
                    """, 1374天趋势
                    """, 2060天趋势
                    """, 3090天趋势
                    """, 4635天趋势
                    """, 695天趋势
                    """, 1043天趋势
                    """, 1565天趋势
                    """, 2348天趋势
                    """, 353天趋势
                    """, 530天趋势
                    """, 795天趋势
                    """, 1190天趋势
                    """, 1785天趋势
                    """, 2683天趋势
                    """, 4025天趋势
                    """, 603天趋势
                    """, 905天趋势
                    """, 1357天趋势
                    "", 2035天趋势
                    """, 3050天趋势
                    """, 4575天趋势
                    "", 684天趋势
                    """, 1022天趋势
                    """, 1533天趋势
                    """, 2299天趋势
                    """, 3448天趋势
                    """, 516天趋势
                    """, 770天趋势
                    """, 1155天趋势
                    """, 1730天趋势
                    """, 2595天趋势
                    "", 3883天趋势
                    """, 5775天趋势
                    """, 866天趋势
                    "", 1299天趋势
                    """, 1947天趋势
                    """, 2916天趋势
                    """, 4374天趋势
                    """, 656天趋势
                    """, 984天趋势
                    """, 1476天趋势
                    """, 2210天趋势
                    """, 3315天趋势
                    """, 4972天趋势
                    "", 7458天趋势
                    """, 1093天趋势
                    """, 1640天趋势
                    """, 2464天趋势
                    """, 3687天趋势
                    """, 5510天趋势
                    """, 8265天趋势
                    """, 1238天趋势
                    """, 1853天趋势
                    """, 2774天趋势
                    "", 4158天趋势
                    "", 6237天趋势
                    """, 939天趋势
                    """, 1408天趋势
                    """, 2106天趋势
                    """, 3150天趋势
                    """, 4725天趋势
                    "", 7085天趋势
                    """, 1062天趋势
                    """, 1593天趋势
                    """, 2389天趋势
                    """, 3583天趋势
                    """, 5374天趋势
                    "", 8064天趋势
                    """, 1215天趋势
                    """, 1823天趋势
                    """, 2734天趋势
                    "", 4099天趋势
                    "", 6165天趋势
                    """, 9248天趋势
                    """, 1387天趋势
                    """, 2076天趋势
                    """, 3114天趋势
                    """, 4672天趋势
                    "", 7008天趋势
                    """, 1051天趋势
                    """, 1576天趋势
                    """, 2364天趋势
                    """, 3546天趋势
                    "", 5317天趋势
                    """, 7908天趋势
                    """, 1186天趋势
                    """, 1779天趋势
                    """, 2669天趋势
                    """, 4000天趋势
                    """, 6000天趋势
                    """, 9000天趋势
                    """, 13500天趋势
                    """, 20250天趋势
                    """, 3000天趋势
                    """, 4500天趋势
                    """, 6750天趋势
                    """, 10125天趋势
                    """, 15188天趋势
                    """, 2274天趋势
                    """, 3411天趋势
                    """, 5117天趋势
                    """, 7670天趋势
                    """, 1150天趋势
                    """, 1730天趋势
                    """, 2595天趋势
                    """, 3883天趋势
                    "", 5807天趋势
                    """, 8712天趋势
                    """, 1300天趋势
                    """, 1950天趋势
                    """, 2600天趋势
                    """, 3900天趋势
                    """, 5850天趋势
                    "", 8775天趋势
                    "", 1316天趋势
                    """, 1974天趋势
                    """, 2960天趋势
                    """, 4440天趋势
                    """, 6660天趋势
                    """, 9990天趋势
                    """, 1498天趋势
                    """, 2247天趋势
                    """, 3371天趋势
                    """, 5057天趋势
                    """, 7586天趋势
                    "", 1117天趋势
                    "", 1674天趋势
                    "", 2511天趋势
                    "", 3348天趋势
                    """, 5030天趋势
                    "", 7545天趋势
                    "", 1131天趋势
                    "", 1697天趋势
                    "", 2544天趋势
                    "", 3395天趋势
                    """, 5091天趋势
                    "", 7637天趋势
                    "", 1146天趋势
                    "", 1724天趋势
                    "", 2588天趋势
                    "", 3880天趋势
                    "", 5800天趋势
                    "", 8712天趋势
                    "", 1304天趋势
                    "", 1950天趋势
                    "", 2600天趋势
                        """, 3900天趋势
                        """, 5850天趋势
                        """, 8775天趋势
                        """, 1316天趋势
                        """, 1974天趋势
                        """, 2960天趋势
                        """, 4440天趋势
                        """, 6660天趋势
                        """, 9990天趋势
                        """, 1498天趋势
                        """, 2247天趋势
                        """, 3371天趋势
                        """, 5057天趋势
                        """, 7586天趋势
                        """, 1117天趋势
                        """, 1674天趋势
                        """, 2512天趋势
                        """, 3350天趋势
                        """, 5030天趋势
                        """, 7545天趋势
                        """, 1127天趋势
                        """, 1688天趋势
                        """, 2536天趋势
                        """, 3384天趋势
                        """, 5045天趋势
                        """, 7573天趋势
                        """, 1129天趋势
                        """, 1687天趋势
                        """, 2528天趋势
                        """, 3392天趋势
                        """, 5088天趋势
                        """, 7632天趋势
                        """, 1144天趋势
                        """, 1716天趋势
                        """, 2574天趋势
                        """, 3864天趋势
                        "" | 5775天趋势
                        ""| 8660天趋势
                        ""| 1299天趋势
                        ""| 1947天趋势
                        ""| 2916天趋势
                        ""| 4374天趋势
                        ""| 6560天趋势
                        ""| 984天趋势
                        ""| 1476天趋势
                        ""| 2210天趋势
                        ""| 3315天趋势
                        ""| 4972天趋势
                        ""| 7458天趋势
                        ""| 1093天趋势
                        ""| 1640天趋势
                        ""| 2464天趋势
                        ""| 3687天趋势
                        ""| 5510天趋势
                        ""| 8265天趋势
                        ""| 1238天趋势
                        ""| 1853天趋势
                        ""| 2774天趋势
                        ""| 4158天趋势
                        ""| 6237天趋势
                        ""| 939天趋势
                        ""| 1408天趋势
                        ""| 2106天趋势
                        ""| 3150天趋势
                        ""| 4725天趋势
                        ""| 7085天趋势
                        ""| 1062天趋势
                        ""| 1593天趋势
                        ""| 2389天趋势
                        ""| 3583天趋势
                        ""| 5374天趋势
                        ""| 8064天趋势
                        ""| 1215天趋势
                        ""| 1823天趋势
                        ""| 2734天趋势
                        ""| 4099天趋势
                        ""| 6165天趋势
                        ""| 9248天趋势
                        ""| 1387天趋势
                        ""| 2076天趋势
                        ""| 3114天趋势
                        ""| 4672天趋势
                        ""| 7008天趋势
                        ""| 1051天趋势
                        ""| 1576天趋势
                        ""| 2364天趋势
                        ""| 3546天趋势
                        ""| 5317天趋势
                        ""| 7908天趋势
                        ""| 1186天趋势
                        ""| 1779天趋势
                        ""| 2669天趋势
                        ""| 4000天趋势
                        ""| 6000天趋势
                        ""| 9000天趋势
                        ""| 13500天趋势
                        ""| 2025天趋势
                        ""| 3000天趋势
                        ""| 4500天趋势
                        ""| 6750天趋势
                        ""| 10125天趋势
                        ""| 15188天趋势
                        ""| 2274天趋势
                        ""| 3411天趋势
                        ""| 5130天趋势
                        ""| 7695天趋势
                        ""| 1155天趋势
                        ""| 1730天趋势
                        ""| 2595天趋势
                        ""| 3883天趋势
                        ""| 5827天趋势
                        ""| 8775天趋势
                        ""| 1316天趋势
                        ""| 1974天趋势
                        ""| 2960天趋势
                        ""| 4440天趋势
                        ""| 6660天趋势
                        ""| 9990天趋势
                        ""| 1498天趋势
                        ""| 2247天趋势
                        ""| 3371天趋势
                        ""| 5057天趋势
                        ""| 7586天趋势
                        ""| 1117天趋势
                        ""| 1674天趋势
                        ""| 2512天趋势
                        ""| 3355天趋势
                        ""| 5030天趋势
                        ""| 7545天趋势
                        ""| 1127天趋势
                        ""| 1688天趋势
                        ""| 2528天趋势
                        ""| 3385天趋势
                        ""| 5075天趋势
                        ""| 7615天趋势
                        ""| 1142天趋势
                        ""| 1713天趋势
                        ""| 2573天趋势
                        ""| 3857天趋势
                        ""| 5785天趋势
                        ""| 8675天趋势
                        ""| 1301天趋势
                        ""| 1950天趋势
                        ""| 2925天趋势
                        ""| 4385天趋势
                        ""| 6575天趋势
                        ""| 9845天趋势
                        ""| 1476天趋势
                        ""| 2210天趋势
                        ""| 3315天趋势
                        ""| 4972天趋势
                        ""| 7458天趋势
                        ""| 1093天趋势
                        ""| 1640天趋势
                        ""| 2464天趋势
                        ""| 3687天趋势
                        ""| 5530天趋势
                        ""| 8292天趋势
                        ""| 1238天趋势
                        ""| 1847天趋势
                        ""| 2764天趋势
                        ""| 4112天趋势
                        ""| 6165天趋势
                        ""| 9248天趋势
                        ""| 1387天趋势
                        ""| 2076天趋势
                        ""| 3114天趋势
                        ""| 4672天趋势
                        ""| 7008天趋势
                        ""| 1051天趋势
                        ""| 1576天趋势
                        ""| 2364天趋势
                        ""| 3546天趋势
                        ""| 5317天趋势
                        ""| 7908天趋势
                        ""| 1186天趋势
                        ""| 1779天趋势
                        ""| 2669天趋势
                        ""| 4000天趋势
                        ""| 6000天趋势
                        ""| 9000天趋势
                        ""| 13500天趋势
                        ""| 2025天趋势
                        ""| 3000天趋势
                        ""| 4500天趋势
                        ""| 6750天趋势
                        ""| 10125天趋势
                        ""| 15188天趋势
                        ""| 2274天趋势
                        ""| 3411天趋势
                        ""| 5130天趋势
                        ""| 7695天趋势
                        ""| 1155天趋势
                        ""| 1730天趋势
                        ""| 2595天趋势
                        ""| 3883天趋势
                        ""| 5827天趋势
                        ""| 8775天趋势
                        ""| 1316天趋势
                        ""| 1974天趋势
                        ""| 2960天趋势
                        ""| 4440天趋势
                        ""| 6660天趋势
                        ""| 9990天趋势
                        ""| 1498天趋势
                        ""| 2247天趋势
                        ""| 3371天趋势
                        ""| 5057天趋势
                        ""| 7586天趋势
                        ""| 1117天趋势
                        ""| 1674天趋势
                        ""| 2512天趋势
                        ""| 3355天趋势
                        ""| 5030天趋势
                        ""| 7545天趋势
                        ""| 1127天趋势
                        ""| 1688天趋势
                        ""| 2528天趋势
                        ""| 3385天趋势
                        ""| 5088天趋势
                        ""| 7632天趋势
                        ""| 1144天趋势
                        ""| 1716天趋势
                        ""| 2574天趋势
                        ""| 3864天趋势
                        ""| 5785天趋势
                        ""| 8675天趋势
                        ""| 1301天趋势
                        ""| 1951天趋势
                        ""| 2600天趋势
                        ""| 3900天趋势
                        ""| 5850天趋势
                        ""| 8775天趋势
                        ""| 1316天趋势
                        ""| 1974天趋势
                        ""| 2960天趋势
                        ""| 4440天趋势
                        ""| 6660天趋势
                        ""| 9990天趋势
                        ""| 1498天趋势
                        ""| 2247天趋势
                        ""| 3371天趋势
                        ""| 5057天趋势
                        ""| 7586天趋势
                        ""| 1117天趋势
                        ""| 1674天趋势
                        ""| 2512天趋势
                        ""| 3355天趋势
                        ""| 5030天趋势
                        ""| 7545天趋势
                        ""| 1127天趋势
                        ""| 1688天趋势
                        ""| 2528天趋势
                        ""| 3385天趋势
                        ""| 5088天趋势
                        ""| 7632天趋势
                        ""| 1144天趋势
                        ""| 1716天趋势
                        ""| 2574天趋势
                        ""| 3864天趋势
                        ""| 5807天趋势
                        ""| 8712天趋势
                        ""| 1304天趋势
                        ""| 1950天趋势
                        ""| 2600天趋势
                        ""| 3900天趋势
                        ""| 5850天趋势
                        ""| 8775天趋势
                        ""| 1316天趋势
                        ""| 1974天趋势
                        ""| 2960天趋势
                        ""| 4440天趋势
                        ""| 6660天趋势
                        ""| 9990天趋势
                        ""| 1498天趋势
                        ""| 2247天趋势
                        ""| 3371天趋势
                        ""| 5057天趋势
                        ""| 7586天趋势
                        ""| 1117天趋势
                        ""| 1674天趋势
                        ""| 2512天趋势
                        ""| 3355天趋势
                        ""| 5030天趋势
                        ""| 7545天趋势
                        ""| 1127天趋势
                        ""| 1688天趋势
                        ""| 2528天趋势
                        ""| 3384天趋势
                        ""| 5045天趋势
                        ""| 7573天趋势
                        ""| 1131天趋势
                        ""| 1697天趋势
                        ""| 2536天趋势
                        ""| 3804天趋势
                        ""| 5712天趋势
                        ""| 8576天趋势
                        ""| 1284天趋势
                        ""| 1926天趋势
                        ""| 2890天趋势
                        ""| 4335天趋势
                        ""| 6502天趋势
                        ""| 9753天趋势
                        ""| 14630天趋势
                    ]
                }
                
                await conn.execute("""
                    INSERT INTO attack_trend_weekly
                    (week_start, week_end, attack_counts, attack_type_distribution)
                    VALUES ($1, $2, $3, $4, $5)
                """, week_start, week_end)
                
                await conn.execute("""
                    INSERT INTO attack_trend_monthly
                    (month_start, month_end, attack_counts, attack_type_distribution)
                    VALUES ($1, $2, $3, $4, $5)
                """, month_start, month_end)
                
                await conn.execute("""
                    INSERT INTO attack_trend_daily
                    (stat_date, attack_counts, attack_type_distribution)
                    VALUES ($1, $2, $3, $4, $5)
                """, stat_date)
                
                await conn.execute("""
                    INSERT INTO response_time_daily
                    (stat_date, avg_response_time_ms, p50_response_time_ms, 
                     p95_response_time_ms, p99_response_time_ms, max_response_time_ms)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, stat_date)
                
                await conn.execute("""
                    INSERT INTO service_availability_daily
                    (stat_date, availability_rate, downtime_seconds, incident_count)
                    VALUES ($1, $2, $3, $4)
                """, stat_date)
                
                await conn.execute("""
                    INSERT INTO training_progress_daily
                    (stat_date, total_episodes, best_win_rate, avg_reward, model_version)
                    VALUES ($1, $2, $3, $4, $5)
                """, stat_date)
                
                await conn.execute("""
                    INSERT INTO resource_usage_daily
                    (stat_date, avg_cpu_percent, avg_memory_percent, 
                     disk_usage_percent, network_in_mbps, network_out_mbps)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, stat_date)
                
                await conn.execute("""
                    INSERT INTO model_performance_daily
                    (stat_date, model_version, tpr, fpr, avg_latency_ms)
                    VALUES ($1, $2, $3, $4, $5)
                """, stat_date)
                
                await conn.execute("""
                    INSERT INTO defense_stats_hourly_summary
                    (stat_hour, total_attacks, blocked_attacks, missed_attacks, 
                     false_positives, normal_requests, service_down_events)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, stat_hour)
                
                logger.info(f"Hourly stats saved for {current_hour}")
                
        finally:
            await conn.close()
            break
    
    except Exception as e:
        logger.error(f"Aggregation error: {e}")
        raise self.retry(exc=e)
    
    duration_seconds = time.time() - start_time
    
    return {
        "success": True,
        "task_id": task_id,
        "duration_seconds": duration_seconds,
        "hourly_stats": hourly_stats,
        "daily_stats": daily_stats,
        "weekly_stats": weekly_stats,
        "monthly_stats": monthly_stats
    }
