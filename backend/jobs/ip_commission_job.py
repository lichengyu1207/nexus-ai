"""
IP扶持计划 - 佣金计算定时任务
每天凌晨运行，将状态为pending且已过结算期的佣金记录改为settled，并累加到IP的balance中
"""
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'property_analysis.db')
SETTLEMENT_DAYS = 7  # 订单完成后T+7天结算

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_pending_commissions(conn) -> List[Dict]:
    cursor = conn.cursor()
    settlement_threshold = datetime.now() - timedelta(days=SETTLEMENT_DAYS)
    
    cursor.execute('''
        SELECT c.*, p.base_commission, p.name as ip_name
        FROM ip_commissions c
        JOIN ip_partners p ON c.ip_id = p.id
        WHERE c.status = 'pending'
        AND c.created_at <= ?
        ORDER BY c.created_at ASC
    ''', (settlement_threshold.isoformat(),))
    
    return [dict(row) for row in cursor.fetchall()]

def settle_commission(conn, commission: Dict) -> bool:
    try:
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ip_commissions 
            SET status = 'settled', settled_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), commission['id']))
        
        cursor.execute('''
            UPDATE ip_partners 
            SET balance = balance + ?,
                total_earned = total_earned + ?,
                updated_at = ?
            WHERE id = ?
        ''', (commission['commission_amount'], commission['commission_amount'], 
              datetime.now().isoformat(), commission['ip_id']))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error settling commission {commission['id']}: {e}")
        conn.rollback()
        return False

def calculate_tier_bonus(conn, ip_id: str) -> float:
    cursor = conn.cursor()
    
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    cursor.execute('''
        SELECT SUM(commission_amount) as total_monthly
        FROM ip_commissions
        WHERE ip_id = ?
        AND status = 'settled'
        AND settled_at >= ?
    ''', (ip_id, month_start.isoformat()))
    
    result = cursor.fetchone()
    monthly_total = result['total_monthly'] or 0
    
    cursor.execute('''
        SELECT * FROM ip_commission_rules
        WHERE rule_type = 'tier_bonus'
        ORDER BY min_amount DESC
    ''')
    tier_rules = [dict(row) for row in cursor.fetchall()]
    
    bonus_rate = 0
    for rule in tier_rules:
        if monthly_total >= rule['min_amount']:
            bonus_rate = rule['bonus_rate']
            break
    
    return bonus_rate

def process_monthly_tier_bonus(conn):
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ip_id, SUM(commission_amount) as monthly_total
        FROM ip_commissions
        WHERE status = 'settled'
        AND settled_at >= ?
        GROUP BY ip_id
    ''', (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat(),))
    
    ip_monthly_totals = [dict(row) for row in cursor.fetchall()]
    
    for ip_data in ip_monthly_totals:
        bonus_rate = calculate_tier_bonus(conn, ip_data['ip_id'])
        if bonus_rate > 0:
            bonus_amount = ip_data['monthly_total'] * bonus_rate / 100
            
            bonus_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO ip_commissions 
                (id, ip_id, order_amount, commission_rate, commission_amount, status, notes, created_at, settled_at)
                VALUES (?, ?, ?, ?, ?, 'settled', ?, ?, ?)
            ''', (bonus_id, ip_data['ip_id'], 0, bonus_rate, bonus_amount, 
                  f'月度阶梯奖励 (+{bonus_rate}%)', datetime.now().isoformat(), datetime.now().isoformat()))
            
            cursor.execute('''
                UPDATE ip_partners 
                SET balance = balance + ?,
                    total_earned = total_earned + ?,
                    updated_at = ?
                WHERE id = ?
            ''', (bonus_amount, bonus_amount, datetime.now().isoformat(), ip_data['ip_id']))
            
            logger.info(f"Added tier bonus {bonus_amount:.2f} to IP {ip_data['ip_id']}")
    
    conn.commit()

def update_ip_levels(conn):
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ip.id, ip.total_earned, ip.total_referrals,
               l.min_earnings, l.min_referrals, l.level_name
        FROM ip_partners ip
        LEFT JOIN ip_levels l ON 1=1
        WHERE ip.status = 'active'
        ORDER BY ip.id, l.min_earnings DESC
    ''')
    
    ip_level_data = {}
    for row in cursor.fetchall():
        row_dict = dict(row)
        ip_id = row_dict['id']
        if ip_id not in ip_level_data:
            ip_level_data[ip_id] = row_dict
    
    for ip_id, data in ip_level_data.items():
        if data['min_earnings'] is not None:
            if data['total_earned'] >= data['min_earnings'] and \
               (data['min_referrals'] is None or data['total_referrals'] >= data['min_referrals']):
                cursor.execute('''
                    UPDATE ip_partners 
                    SET level = ?, updated_at = ?
                    WHERE id = ? AND level != ?
                ''', (data['level_name'], datetime.now().isoformat(), ip_id, data['level_name']))
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated IP {ip_id} to level {data['level_name']}")
    
    conn.commit()

def log_operation(conn, operation: str, details: str):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ip_operation_logs (id, operation, details, created_at)
        VALUES (?, ?, ?, ?)
    ''', (str(uuid.uuid4()), operation, details, datetime.now().isoformat()))
    conn.commit()

def run_commission_job():
    logger.info(f"Starting commission settlement job at {datetime.now()}")
    
    conn = get_db_connection()
    
    try:
        pending_commissions = get_pending_commissions(conn)
        logger.info(f"Found {len(pending_commissions)} pending commissions to settle")
        
        settled_count = 0
        total_amount = 0
        
        for commission in pending_commissions:
            if settle_commission(conn, commission):
                settled_count += 1
                total_amount += commission['commission_amount']
                logger.info(f"Settled commission {commission['id']} for IP {commission['ip_name']}: {commission['commission_amount']:.2f}")
        
        process_monthly_tier_bonus(conn)
        
        update_ip_levels(conn)
        
        log_operation(conn, 'commission_settlement', 
                     f'Settled {settled_count} commissions, total amount: {total_amount:.2f}')
        
        logger.info(f"Commission settlement completed. Settled {settled_count} commissions, total: {total_amount:.2f}")
        
        return {
            'success': True,
            'settled_count': settled_count,
            'total_amount': total_amount
        }
        
    except Exception as e:
        logger.error(f"Commission settlement job failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        conn.close()

def run_with_expiration_check():
    cursor = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        expiration_days = 30
        expiration_threshold = datetime.now() - timedelta(days=expiration_days)
        
        cursor.execute('''
            UPDATE ip_referrals 
            SET status = 'expired'
            WHERE status = 'active'
            AND clicked_at IS NOT NULL
            AND clicked_at <= ?
            AND registered_at IS NULL
        ''', (expiration_threshold.isoformat(),))
        
        expired_count = cursor.rowcount
        conn.commit()
        
        if expired_count > 0:
            logger.info(f"Marked {expired_count} expired referrals")
        
        return expired_count
        
    except Exception as e:
        logger.error(f"Expiration check failed: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    result = run_commission_job()
    print(f"Commission job result: {result}")
    
    expired = run_with_expiration_check()
    print(f"Expired referrals: {expired}")
