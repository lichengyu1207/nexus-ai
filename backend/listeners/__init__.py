"""
事件监听器模块
"""
from .stats_listeners import (
    register_listeners,
    handle_user_registered,
    handle_user_location_updated,
    handle_integral_changed,
    handle_task_created,
    handle_task_completed,
    handle_signin,
    update_source_stats,
    update_city_stats,
    update_district_stats,
    update_user_behavior_stats
)

__all__ = [
    'register_listeners',
    'handle_user_registered',
    'handle_user_location_updated',
    'handle_integral_changed',
    'handle_task_created',
    'handle_task_completed',
    'handle_signin',
    'update_source_stats',
    'update_city_stats',
    'update_district_stats',
    'update_user_behavior_stats'
]
