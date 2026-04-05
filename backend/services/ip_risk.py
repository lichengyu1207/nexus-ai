"""
IP扶持计划 - 风控服务
提供方法检查推广用户是否可疑，识别异常流量和作弊行为
"""
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'property_analysis.db')

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskTag(Enum):
    SAME_IP_MULTIPLE_REGISTRATIONS = "same_ip_multiple_registrations"
    RAPID_REGISTRATIONS = "rapid_registrations"
    IMMEDIATE_LARGE_ORDER = "immediate_large_order"
    IP_SELF_REFERRAL = "ip_self_referral"
    SUSPICIOUS_DEVICE = "suspicious_device"
    BLACKLISTED_IP = "blacklisted_ip"
    BLACKLISTED_DEVICE = "blacklisted_device"
    ABNORMAL_PATTERN = "abnormal_pattern"
    LOW_QUALITY_TRAFFIC = "low_quality_traffic"

@dataclass
class RiskAssessment:
    risk_level: RiskLevel
    risk_tags: List[RiskTag]
    risk_score: int
    details: Dict
    recommendation: str

class IPRiskService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.config = self._load_config()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_config(self) -> Dict:
        default_config = {
            "same_ip_threshold": 3,
            "same_ip_timeframe_hours": 24,
            "rapid_registration_threshold": 5,
            "rapid_registration_timeframe_minutes": 60,
            "immediate_order_threshold": 100,
            "immediate_order_timeframe_hours": 1,
            "low_quality_threshold": 0.1,
            "blacklist_check_enabled": True,
            "auto_block_critical": True,
            "auto_suspend_high": False
        }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT config_value FROM ip_commission_rules
                WHERE rule_type = 'risk_config'
            ''')
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {**default_config, **json.loads(result['config_value'])}
        except Exception as e:
            logger.warning(f"Could not load risk config, using defaults: {e}")
        
        return default_config
    
    def check_user_risk(self, user_id: str, ip_id: str, 
                        ip_address: str = None, 
                        device_id: str = None,
                        order_amount: float = None) -> RiskAssessment:
        risk_tags = []
        risk_score = 0
        details = {}
        
        if self._check_blacklist(ip_address, device_id):
            risk_tags.append(RiskTag.BLACKLISTED_IP)
            risk_score += 100
            details['blacklisted'] = True
        
        if ip_address:
            same_ip_count = self._check_same_ip_registrations(ip_address, ip_id)
            if same_ip_count >= self.config['same_ip_threshold']:
                risk_tags.append(RiskTag.SAME_IP_MULTIPLE_REGISTRATIONS)
                risk_score += 30
                details['same_ip_count'] = same_ip_count
        
        rapid_count = self._check_rapid_registrations(ip_id)
        if rapid_count >= self.config['rapid_registration_threshold']:
            risk_tags.append(RiskTag.RAPID_REGISTRATIONS)
            risk_score += 25
            details['rapid_registration_count'] = rapid_count
        
        if self._check_ip_self_referral(user_id, ip_id):
            risk_tags.append(RiskTag.IP_SELF_REFERRAL)
            risk_score += 50
            details['self_referral'] = True
        
        if order_amount and order_amount >= self.config['immediate_order_threshold']:
            if self._check_immediate_large_order(user_id, order_amount):
                risk_tags.append(RiskTag.IMMEDIATE_LARGE_ORDER)
                risk_score += 40
                details['immediate_large_order'] = True
                details['order_amount'] = order_amount
        
        conversion_rate = self._calculate_conversion_rate(ip_id)
        if conversion_rate < self.config['low_quality_threshold']:
            risk_tags.append(RiskTag.LOW_QUALITY_TRAFFIC)
            risk_score += 15
            details['conversion_rate'] = conversion_rate
        
        if self._check_abnormal_pattern(user_id, ip_id):
            risk_tags.append(RiskTag.ABNORMAL_PATTERN)
            risk_score += 20
            details['abnormal_pattern'] = True
        
        risk_level = self._calculate_risk_level(risk_score)
        recommendation = self._generate_recommendation(risk_level, risk_tags)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_tags=risk_tags,
            risk_score=risk_score,
            details=details,
            recommendation=recommendation
        )
    
    def _check_blacklist(self, ip_address: str = None, device_id: str = None) -> bool:
        if not self.config['blacklist_check_enabled']:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if ip_address:
                cursor.execute('''
                    SELECT 1 FROM ip_risk_blacklist 
                    WHERE (ip_address = ? OR ip_address = '*')
                    AND status = 'active'
                ''', (ip_address,))
                if cursor.fetchone():
                    return True
            
            if device_id:
                cursor.execute('''
                    SELECT 1 FROM ip_risk_blacklist 
                    WHERE device_id = ?
                    AND status = 'active'
                ''', (device_id,))
                if cursor.fetchone():
                    return True
            
            return False
        finally:
            conn.close()
    
    def _check_same_ip_registrations(self, ip_address: str, ip_id: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            timeframe = datetime.now() - timedelta(hours=self.config['same_ip_timeframe_hours'])
            
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM ip_referrals r
                JOIN users u ON r.user_id = u.id
                WHERE r.ip_id = ?
                AND u.registration_ip = ?
                AND r.registered_at >= ?
            ''', (ip_id, ip_address, timeframe.isoformat()))
            
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()
    
    def _check_rapid_registrations(self, ip_id: str) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            timeframe = datetime.now() - timedelta(minutes=self.config['rapid_registration_timeframe_minutes'])
            
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM ip_referrals
                WHERE ip_id = ?
                AND registered_at >= ?
            ''', (ip_id, timeframe.isoformat()))
            
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()
    
    def _check_ip_self_referral(self, user_id: str, ip_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 1 FROM ip_partners WHERE id = ? AND user_id = ?
            ''', (ip_id, user_id))
            
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def _check_immediate_large_order(self, user_id: str, order_amount: float) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            timeframe = datetime.now() - timedelta(hours=self.config['immediate_order_timeframe_hours'])
            
            cursor.execute('''
                SELECT created_at FROM users WHERE id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False
            
            registration_time = datetime.fromisoformat(user['created_at'])
            hours_since_registration = (datetime.now() - registration_time).total_seconds() / 3600
            
            return hours_since_registration <= self.config['immediate_order_timeframe_hours']
        finally:
            conn.close()
    
    def _calculate_conversion_rate(self, ip_id: str) -> float:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN first_order_at IS NOT NULL THEN 1 ELSE 0 END) as converted
                FROM ip_referrals
                WHERE ip_id = ?
                AND registered_at >= ?
            ''', (ip_id, (datetime.now() - timedelta(days=30)).isoformat()))
            
            result = cursor.fetchone()
            if not result or result['total_referrals'] == 0:
                return 1.0
            
            return result['converted'] / result['total_referrals']
        finally:
            conn.close()
    
    def _check_abnormal_pattern(self, user_id: str, ip_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT l.click_count, l.created_at
                FROM ip_links l
                JOIN ip_referrals r ON r.link_id = l.id
                WHERE r.ip_id = ? AND r.user_id = ?
                ORDER BY l.created_at DESC
                LIMIT 1
            ''', (ip_id, user_id))
            
            link = cursor.fetchone()
            if not link:
                return False
            
            if link['click_count'] > 100:
                return True
            
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM ip_referrals
                WHERE ip_id = ?
                AND registered_at >= ?
            ''', (ip_id, (datetime.now() - timedelta(hours=1)).isoformat()))
            
            recent = cursor.fetchone()
            if recent and recent['count'] > 20:
                return True
            
            return False
        finally:
            conn.close()
    
    def _calculate_risk_level(self, risk_score: int) -> RiskLevel:
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendation(self, risk_level: RiskLevel, risk_tags: List[RiskTag]) -> str:
        if risk_level == RiskLevel.CRITICAL:
            return "建议立即暂停佣金结算，进行人工审核"
        elif risk_level == RiskLevel.HIGH:
            return "建议标记为可疑，延迟结算并人工审核"
        elif risk_level == RiskLevel.MEDIUM:
            return "建议监控该用户后续行为，必要时人工审核"
        else:
            return "正常，可以自动结算"
    
    def add_to_blacklist(self, ip_address: str = None, device_id: str = None, 
                         reason: str = None, admin_id: str = None) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            import uuid
            cursor.execute('''
                INSERT INTO ip_risk_blacklist 
                (id, ip_address, device_id, reason, added_by, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?)
            ''', (str(uuid.uuid4()), ip_address, device_id, reason, admin_id, 
                  datetime.now().isoformat()))
            
            conn.commit()
            logger.info(f"Added to blacklist: IP={ip_address}, Device={device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add to blacklist: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def remove_from_blacklist(self, item_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE ip_risk_blacklist 
                SET status = 'inactive', updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), item_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to remove from blacklist: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_suspicious_ips(self, days: int = 7) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    ip_id,
                    COUNT(*) as suspicious_count,
                    GROUP_CONCAT(user_id) as user_ids
                FROM ip_referrals
                WHERE status = 'suspicious'
                AND registered_at >= ?
                GROUP BY ip_id
                ORDER BY suspicious_count DESC
            ''', ((datetime.now() - timedelta(days=days)).isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def mark_referral_suspicious(self, referral_id: str, reason: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE ip_referrals 
                SET status = 'suspicious', notes = ?
                WHERE id = ?
            ''', (reason, referral_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark referral suspicious: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

risk_service = IPRiskService()

def check_user_risk(user_id: str, ip_id: str, 
                    ip_address: str = None, 
                    device_id: str = None,
                    order_amount: float = None) -> RiskAssessment:
    return risk_service.check_user_risk(user_id, ip_id, ip_address, device_id, order_amount)

def add_to_blacklist(ip_address: str = None, device_id: str = None, 
                     reason: str = None, admin_id: str = None) -> bool:
    return risk_service.add_to_blacklist(ip_address, device_id, reason, admin_id)

def get_suspicious_ips(days: int = 7) -> List[Dict]:
    return risk_service.get_suspicious_ips(days)
