"""
积分日志记录服务
用于在每次积分变动时记录日志，包含时间戳、Token换算、关联资源等字段
"""
import sqlite3
import os
import uuid
import logging
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

TOKEN_MULTIPLIER = 100  # 1积分 = 100 Token

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def record_integral_log(
    user_id: str,
    change: float,
    balance_after: float,
    reason: str,
    action_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    admin_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None
) -> dict:
    log_id = str(uuid.uuid4())
    token_change = int(change * TOKEN_MULTIPLIER)
    token_balance_after = int(balance_after * TOKEN_MULTIPLIER)
    created_at = datetime.now().isoformat()
    
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO integral_logs 
            (id, user_id, change, balance_after, token_change, token_balance_after, 
             reason, action_type, resource_id, resource_type, admin_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log_id, user_id, change, balance_after, token_change, token_balance_after,
              reason, action_type, resource_id, resource_type, admin_id, created_at))
        
        if close_conn:
            conn.commit()
        
        logger.info(f"Recorded integral log: user={user_id}, change={change}, reason={reason}")
        
        return {
            'id': log_id,
            'user_id': user_id,
            'change': change,
            'balance_after': balance_after,
            'token_change': token_change,
            'token_balance_after': token_balance_after,
            'reason': reason,
            'action_type': action_type,
            'resource_id': resource_id,
            'resource_type': resource_type,
            'created_at': created_at
        }
    except Exception as e:
        logger.error(f"Failed to record integral log: {e}")
        if close_conn:
            conn.rollback()
        raise
    finally:
        if close_conn:
            conn.close()

def get_user_integral_logs(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action_type: Optional[str] = None
) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        
        where_clauses = ['user_id = ?']
        params = [user_id]
        
        if start_date:
            where_clauses.append('created_at >= ?')
            params.append(start_date)
        
        if end_date:
            where_clauses.append('created_at <= ?')
            params.append(end_date)
        
        if action_type:
            where_clauses.append('action_type = ?')
            params.append(action_type)
        
        where_sql = ' AND '.join(where_clauses)
        
        count_sql = f'SELECT COUNT(*) as total FROM integral_logs WHERE {where_sql}'
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        offset = (page - 1) * limit
        data_sql = f'''
            SELECT * FROM integral_logs 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        cursor.execute(data_sql, params + [limit, offset])
        logs = [dict(row) for row in cursor.fetchall()]
        
        return {
            'logs': logs,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        }

def get_user_integral_balance(user_id: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT integral, token_balance 
            FROM users WHERE id = ?
        ''', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {'integral': 0, 'tokens': 0}
        
        integral = user['integral'] or 0
        tokens = int(integral * TOKEN_MULTIPLIER)
        
        return {
            'integral': integral,
            'tokens': tokens
        }

def consume_integral(
    user_id: str,
    amount: float,
    reason: str,
    action_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        current_balance = user['integral'] or 0
        
        if current_balance < amount:
            raise ValueError(f"Insufficient balance: {current_balance} < {amount}")
        
        new_balance = current_balance - amount
        
        cursor.execute('UPDATE users SET integral = ? WHERE id = ?', (new_balance, user_id))
        
        log = record_integral_log(
            user_id=user_id,
            change=-amount,
            balance_after=new_balance,
            reason=reason,
            action_type=action_type,
            resource_id=resource_id,
            resource_type=resource_type,
            conn=conn
        )
        
        conn.commit()
        
        return {
            'old_balance': current_balance,
            'new_balance': new_balance,
            'consumed': amount,
            'consumed_tokens': int(amount * TOKEN_MULTIPLIER),
            'remaining_tokens': int(new_balance * TOKEN_MULTIPLIER),
            'log': log
        }

def add_integral(
    user_id: str,
    amount: float,
    reason: str,
    action_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    admin_id: Optional[str] = None
) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT integral FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        current_balance = user['integral'] or 0
        new_balance = current_balance + amount
        
        cursor.execute('UPDATE users SET integral = ? WHERE id = ?', (new_balance, user_id))
        
        log = record_integral_log(
            user_id=user_id,
            change=amount,
            balance_after=new_balance,
            reason=reason,
            action_type=action_type,
            resource_id=resource_id,
            resource_type=resource_type,
            admin_id=admin_id,
            conn=conn
        )
        
        conn.commit()
        
        return {
            'old_balance': current_balance,
            'new_balance': new_balance,
            'added': amount,
            'added_tokens': int(amount * TOKEN_MULTIPLIER),
            'new_tokens': int(new_balance * TOKEN_MULTIPLIER),
            'log': log
        }

def get_integral_stats(user_id: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN change > 0 THEN change ELSE 0 END) as total_earned,
                SUM(CASE WHEN change < 0 THEN ABS(change) ELSE 0 END) as total_consumed,
                COUNT(CASE WHEN change > 0 THEN 1 END) as earn_count,
                COUNT(CASE WHEN change < 0 THEN 1 END) as consume_count
            FROM integral_logs WHERE user_id = ?
        ''', (user_id,))
        
        stats = cursor.fetchone()
        
        return {
            'total_earned': stats['total_earned'] or 0,
            'total_consumed': stats['total_consumed'] or 0,
            'earn_count': stats['earn_count'] or 0,
            'consume_count': stats['consume_count'] or 0
        }
