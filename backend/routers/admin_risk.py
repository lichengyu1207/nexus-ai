"""
风控规则管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json

from backend.database import get_db_connection
from backend.auth import require_admin

router = APIRouter(prefix="/api/admin/risk", tags=["admin_risk"])


class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str
    conditions: dict
    action: str
    priority: int = 0
    enabled: bool = True


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[dict] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


@router.get("/rules")
async def get_rules(current_user: dict = Depends(require_admin)):
    """获取所有风控规则"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM risk_rules ORDER BY priority DESC, created_at DESC"
        )
        rules = await cursor.fetchall()
        
        result = []
        for rule in rules:
            rule_dict = dict(rule)
            if isinstance(rule_dict['conditions'], str):
                try:
                    rule_dict['conditions'] = json.loads(rule_dict['conditions'])
                except:
                    pass
            result.append(rule_dict)
        
        return {"rules": result}
    finally:
        await conn.close()


@router.post("/rules")
async def create_rule(
    rule: RuleCreate,
    current_user: dict = Depends(require_admin)
):
    """创建风控规则"""
    if rule.action not in ["mark_suspicious", "require_manual", "reject"]:
        raise HTTPException(status_code=400, detail="无效的action类型")
    
    conn = await get_db_connection()
    try:
        rule_id = str(uuid.uuid4())
        
        await conn.execute(
            "INSERT INTO risk_rules (id, name, description, rule_type, conditions, action, priority, enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (rule_id, rule.name, rule.description, rule.rule_type, json.dumps(rule.conditions), rule.action, rule.priority, 1 if rule.enabled else 0)
        )
        await conn.commit()
        
        return {"status": "success", "rule_id": rule_id}
    finally:
        await conn.close()


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    rule: RuleUpdate,
    current_user: dict = Depends(require_admin)
):
    """更新风控规则"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT id FROM risk_rules WHERE id = ?", (rule_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="规则不存在")
        
        updates = []
        params = []
        
        if rule.name is not None:
            updates.append("name = ?")
            params.append(rule.name)
        if rule.description is not None:
            updates.append("description = ?")
            params.append(rule.description)
        if rule.conditions is not None:
            updates.append("conditions = ?")
            params.append(json.dumps(rule.conditions))
        if rule.action is not None:
            if rule.action not in ["mark_suspicious", "require_manual", "reject"]:
                raise HTTPException(status_code=400, detail="无效的action类型")
            updates.append("action = ?")
            params.append(rule.action)
        if rule.priority is not None:
            updates.append("priority = ?")
            params.append(rule.priority)
        if rule.enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if rule.enabled else 0)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(rule_id)
            
            await conn.execute(
                f"UPDATE risk_rules SET {', '.join(updates)} WHERE id = ?",
                params
            )
            await conn.commit()
        
        return {"status": "success"}
    finally:
        await conn.close()


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: dict = Depends(require_admin)
):
    """删除风控规则"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT id FROM risk_rules WHERE id = ?", (rule_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="规则不存在")
        
        await conn.execute("DELETE FROM risk_rules WHERE id = ?", (rule_id,))
        await conn.commit()
        
        return {"status": "success"}
    finally:
        await conn.close()


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: str,
    current_user: dict = Depends(require_admin)
):
    """切换规则启用状态"""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute("SELECT enabled FROM risk_rules WHERE id = ?", (rule_id,))
        rule = await cursor.fetchone()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        new_enabled = 0 if rule["enabled"] else 1
        await conn.execute(
            "UPDATE risk_rules SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_enabled, rule_id)
        )
        await conn.commit()
        
        return {"status": "success", "enabled": bool(new_enabled)}
    finally:
        await conn.close()


@router.get("/rule-types")
async def get_rule_types(current_user: dict = Depends(require_admin)):
    """获取支持的规则类型"""
    return {
        "types": [
            {"type": "amount_limit", "name": "金额限制", "description": "单笔充值金额超过阈值"},
            {"type": "frequency_limit", "name": "频率限制", "description": "指定时间内充值次数超过阈值"},
            {"type": "new_user", "name": "新用户限制", "description": "新注册用户高额充值"},
            {"type": "duplicate_amount", "name": "重复金额", "description": "短时间内重复提交相同金额"},
            {"type": "amount_anomaly", "name": "金额异常", "description": "充值金额超过历史平均值倍数"},
            {"type": "custom", "name": "自定义规则", "description": "自定义条件规则"}
        ],
        "actions": [
            {"action": "mark_suspicious", "name": "标记可疑"},
            {"action": "require_manual", "name": "人工审核"},
            {"action": "reject", "name": "自动拒绝"}
        ]
    }
