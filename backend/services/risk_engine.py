"""
风控引擎服务
用于检测充值订单的风险等级
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from backend.database import get_db_connection

logger = logging.getLogger(__name__)


class RiskEngine:
    """风控规则引擎"""
    
    def __init__(self):
        self.rules: List[Dict] = []
        self._loaded = False
    
    async def load_rules(self):
        """加载所有启用的风控规则"""
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM risk_rules WHERE enabled = 1 ORDER BY priority DESC"
            )
            rows = await cursor.fetchall()
            self.rules = []
            for row in rows:
                rule = dict(row)
                try:
                    rule['conditions'] = json.loads(rule['conditions']) if isinstance(rule['conditions'], str) else rule['conditions']
                except:
                    rule['conditions'] = {}
                self.rules.append(rule)
            self._loaded = True
            logger.info(f"已加载 {len(self.rules)} 条风控规则")
        finally:
            await conn.close()
    
    async def check_order(self, order_id: str) -> Tuple[str, List[str]]:
        """
        检查订单风险
        返回: (风险等级, 风险标签列表)
        """
        if not self._loaded:
            await self.load_rules()
        
        conn = await get_db_connection()
        try:
            cursor = await conn.execute(
                "SELECT * FROM recharge_orders WHERE id = ?",
                (order_id,)
            )
            order = await cursor.fetchone()
            if not order:
                return 'low', []
            
            order = dict(order)
            user_id = order['user_id']
            
            cursor = await conn.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            user = await cursor.fetchone()
            user = dict(user) if user else {}
            
            risk_tags = []
            risk_score = 0
            
            for rule in self.rules:
                try:
                    matched, score = await self._evaluate_rule(rule, order, user, conn)
                    if matched:
                        risk_tags.append(rule['name'])
                        risk_score += score
                        
                        if rule['action'] == 'reject':
                            return 'high', risk_tags
                except Exception as e:
                    logger.error(f"规则 {rule['name']} 执行失败: {e}")
            
            if risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 20:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return risk_level, risk_tags
            
        finally:
            await conn.close()
    
    async def _evaluate_rule(self, rule: Dict, order: Dict, user: Dict, conn) -> Tuple[bool, int]:
        """评估单条规则"""
        conditions = rule.get('conditions', {})
        rule_type = rule.get('rule_type', '')
        score = 0
        
        if rule_type == 'amount_limit':
            threshold = conditions.get('threshold', 10000)
            if order.get('amount', 0) > threshold:
                score = conditions.get('score', 20)
                return True, score
        
        elif rule_type == 'frequency_limit':
            time_window = conditions.get('time_window', 86400)
            threshold = conditions.get('threshold', 5)
            
            start_time = datetime.utcnow() - timedelta(seconds=time_window)
            cursor = await conn.execute(
                "SELECT COUNT(*) as cnt FROM recharge_orders WHERE user_id = ? AND submitted_at >= ?",
                (order['user_id'], start_time.isoformat())
            )
            result = await cursor.fetchone()
            count = result['cnt'] if result else 0
            
            if count >= threshold:
                score = conditions.get('score', 30)
                return True, score
        
        elif rule_type == 'new_user':
            days = conditions.get('days', 1)
            amount_threshold = conditions.get('amount_threshold', 1000)
            
            created_at = user.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_since_register = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
                
                if days_since_register < days and order.get('amount', 0) > amount_threshold:
                    score = conditions.get('score', 25)
                    return True, score
        
        elif rule_type == 'amount_anomaly':
            multiplier = conditions.get('multiplier', 3)
            
            cursor = await conn.execute(
                "SELECT AVG(amount) as avg_amount FROM recharge_orders WHERE user_id = ? AND status = 'approved'",
                (order['user_id'],)
            )
            result = await cursor.fetchone()
            avg_amount = result['avg_amount'] if result and result['avg_amount'] else 0
            
            if avg_amount > 0 and order.get('amount', 0) > avg_amount * multiplier:
                score = conditions.get('score', 35)
                return True, score
        
        elif rule_type == 'duplicate_amount':
            time_window = conditions.get('time_window', 3600)
            
            start_time = datetime.utcnow() - timedelta(seconds=time_window)
            cursor = await conn.execute(
                "SELECT COUNT(*) as cnt FROM recharge_orders WHERE user_id = ? AND amount = ? AND submitted_at >= ? AND id != ?",
                (order['user_id'], order.get('amount'), start_time.isoformat(), order['id'])
            )
            result = await cursor.fetchone()
            count = result['cnt'] if result else 0
            
            if count > 0:
                score = conditions.get('score', 40)
                return True, score
        
        elif rule_type == 'custom':
            pass
        
        return False, 0
    
    async def update_order_risk(self, order_id: str) -> Tuple[str, List[str]]:
        """更新订单风险等级"""
        risk_level, risk_tags = await self.check_order(order_id)
        
        conn = await get_db_connection()
        try:
            await conn.execute(
                "UPDATE recharge_orders SET risk_level = ?, risk_tags = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (risk_level, json.dumps(risk_tags), order_id)
            )
            await conn.commit()
            logger.info(f"订单 {order_id} 风险等级更新为 {risk_level}, 标签: {risk_tags}")
            return risk_level, risk_tags
        finally:
            await conn.close()


risk_engine = RiskEngine()


async def init_default_rules():
    """初始化默认风控规则"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT COUNT(*) as cnt FROM risk_rules")
        result = await cursor.fetchone()
        
        if result and result['cnt'] > 0:
            return
        
        default_rules = [
            {
                'id': 'rule_amount_high',
                'name': '高额充值预警',
                'description': '单笔充值金额超过10000元',
                'rule_type': 'amount_limit',
                'conditions': json.dumps({'threshold': 10000, 'score': 20}),
                'action': 'mark_suspicious',
                'priority': 100
            },
            {
                'id': 'rule_frequency',
                'name': '频繁充值预警',
                'description': '24小时内充值超过5次',
                'rule_type': 'frequency_limit',
                'conditions': json.dumps({'time_window': 86400, 'threshold': 5, 'score': 30}),
                'action': 'mark_suspicious',
                'priority': 90
            },
            {
                'id': 'rule_new_user',
                'name': '新用户高额充值',
                'description': '注册1天内充值超过1000元',
                'rule_type': 'new_user',
                'conditions': json.dumps({'days': 1, 'amount_threshold': 1000, 'score': 25}),
                'action': 'mark_suspicious',
                'priority': 80
            },
            {
                'id': 'rule_duplicate',
                'name': '重复金额预警',
                'description': '1小时内提交相同金额的充值',
                'rule_type': 'duplicate_amount',
                'conditions': json.dumps({'time_window': 3600, 'score': 40}),
                'action': 'mark_suspicious',
                'priority': 70
            },
            {
                'id': 'rule_anomaly',
                'name': '金额异常预警',
                'description': '充值金额超过历史平均3倍',
                'rule_type': 'amount_anomaly',
                'conditions': json.dumps({'multiplier': 3, 'score': 35}),
                'action': 'mark_suspicious',
                'priority': 60
            }
        ]
        
        for rule in default_rules:
            await conn.execute(
                "INSERT INTO risk_rules (id, name, description, rule_type, conditions, action, priority) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rule['id'], rule['name'], rule['description'], rule['rule_type'], rule['conditions'], rule['action'], rule['priority'])
            )
        
        await conn.commit()
        logger.info("默认风控规则初始化完成")
    finally:
        await conn.close()
