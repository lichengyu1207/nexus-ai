# -*- coding: utf-8 -*-
"""
Point System Service
Manages points, wallets, and transactions
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid


class TransactionType:
    EARN = "earn"
    SPEND = "spend"
    REFUND = "refund"
    TRANSFER = "transfer"
    WITHDRAW = "withdraw"
    FREEZE = "freeze"
    UNFREEZE = "unfreeze"


@dataclass
class PointWallet:
    id: str
    user_id: str
    total_points: int = 0
    available_points: int = 0
    frozen_points: int = 0
    withdrawable_points: int = 0
    lifetime_earned: int = 0
    lifetime_spent: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "PointWallet":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            total_points=row.get("total_points", 0),
            available_points=row.get("available_points", 0),
            frozen_points=row.get("frozen_points", 0),
            withdrawable_points=row.get("withdrawable_points", 0),
            lifetime_earned=row.get("lifetime_earned", 0),
            lifetime_spent=row.get("lifetime_spent", 0),
            created_at=row.get("created_at", datetime.now()),
            updated_at=row.get("updated_at", datetime.now())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_points": self.total_points,
            "available_points": self.available_points,
            "frozen_points": self.frozen_points,
            "withdrawable_points": self.withdrawable_points,
            "lifetime_earned": self.lifetime_earned,
            "lifetime_spent": self.lifetime_spent
        }


@dataclass
class PointTransaction:
    id: str
    user_id: str
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    source: Optional[str] = None
    description: Optional[str] = None
    related_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "PointTransaction":
        return cls(
            id=str(row.get("id", "")),
            user_id=str(row.get("user_id", "")),
            transaction_type=row.get("transaction_type", ""),
            amount=row.get("amount", 0),
            balance_before=row.get("balance_before", 0),
            balance_after=row.get("balance_after", 0),
            source=row.get("source"),
            description=row.get("description"),
            related_id=str(row.get("related_id")) if row.get("related_id") else None,
            metadata=row.get("metadata", {}) or {},
            created_at=row.get("created_at", datetime.now())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "source": self.source,
            "description": self.description,
            "related_id": self.related_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class EarningRule:
    id: str
    action_type: str
    points: int
    daily_limit: int = -1
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_db_row(cls, row: dict) -> "EarningRule":
        return cls(
            id=str(row.get("id", "")),
            action_type=row.get("action_type", ""),
            points=row.get("points", 0),
            daily_limit=row.get("daily_limit", -1),
            description=row.get("description"),
            is_active=row.get("is_active", True),
            created_at=row.get("created_at", datetime.now())
        )


class PointService:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_or_create_wallet(self, user_id: str) -> PointWallet:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM point_wallets WHERE user_id = $1", user_id
            )
            if row:
                return PointWallet.from_db_row(dict(row))
            
            wallet_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO point_wallets (id, user_id, total_points, available_points,
                                          frozen_points, withdrawable_points, lifetime_earned, lifetime_spent)
                VALUES ($1, $2, 0, 0, 0, 0, 0, 0)
            """, wallet_id, user_id)
            
            return PointWallet(
                id=wallet_id,
                user_id=user_id,
                total_points=0,
                available_points=0,
                frozen_points=0,
                withdrawable_points=0,
                lifetime_earned=0,
                lifetime_spent=0
            )

    async def get_balance(self, user_id: str) -> Dict[str, int]:
        wallet = await self.get_or_create_wallet(user_id)
        return {
            "total_points": wallet.total_points,
            "available_points": wallet.available_points,
            "frozen_points": wallet.frozen_points,
            "withdrawable_points": wallet.withdrawable_points
        }

    async def add_points(
        self,
        user_id: str,
        amount: int,
        source: str,
        description: str = None,
        related_id: str = None,
        is_withdrawable: bool = False
    ) -> PointTransaction:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                wallet = await self.get_or_create_wallet(user_id)
                balance_before = wallet.available_points
                balance_after = balance_before + amount
                
                transaction_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO point_transactions (id, user_id, transaction_type, amount,
                                                   balance_before, balance_after, source, description, related_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, transaction_id, user_id, TransactionType.EARN, amount,
                    balance_before, balance_after, source, description, related_id)
                
                update_fields = [
                    "total_points = total_points + $1",
                    "available_points = available_points + $1",
                    "lifetime_earned = lifetime_earned + $1",
                    "updated_at = $2"
                ]
                if is_withdrawable:
                    update_fields.append("withdrawable_points = withdrawable_points + $1")
                
                await conn.execute(
                    f"UPDATE point_wallets SET {', '.join(update_fields)} WHERE user_id = ${3 if is_withdrawable else 2}",
                    amount, datetime.now(), user_id
                )
                
                return PointTransaction(
                    id=transaction_id,
                    user_id=user_id,
                    transaction_type=TransactionType.EARN,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    source=source,
                    description=description,
                    related_id=related_id
                )

    async def deduct_points(
        self,
        user_id: str,
        amount: int,
        source: str,
        description: str = None,
        related_id: str = None
    ) -> PointTransaction:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                wallet = await self.get_or_create_wallet(user_id)
                
                if wallet.available_points < amount:
                    raise ValueError(f"Insufficient points. Available: {wallet.available_points}, Required: {amount}")
                
                balance_before = wallet.available_points
                balance_after = balance_before - amount
                
                transaction_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO point_transactions (id, user_id, transaction_type, amount,
                                                   balance_before, balance_after, source, description, related_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, transaction_id, user_id, TransactionType.SPEND, amount,
                    balance_before, balance_after, source, description, related_id)
                
                await conn.execute("""
                    UPDATE point_wallets 
                    SET available_points = available_points - $1,
                        lifetime_spent = lifetime_spent + $1,
                        updated_at = $2
                    WHERE user_id = $3
                """, amount, datetime.now(), user_id)
                
                return PointTransaction(
                    id=transaction_id,
                    user_id=user_id,
                    transaction_type=TransactionType.SPEND,
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    source=source,
                    description=description,
                    related_id=related_id
                )

    async def transfer_points(
        self,
        from_user_id: str,
        to_user_id: str,
        amount: int,
        description: str = None
    ) -> tuple[PointTransaction, PointTransaction]:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                deduct_tx = await self.deduct_points(
                    from_user_id, amount, "transfer", description, to_user_id
                )
                
                add_tx = await self.add_points(
                    to_user_id, amount, "transfer", description, from_user_id, is_withdrawable=True
                )
                
                return deduct_tx, add_tx

    async def get_transactions(
        self,
        user_id: str,
        transaction_type: str = None,
        start_date: date = None,
        end_date: date = None,
        page: int = 1,
        size: int = 20
    ) -> tuple[List[PointTransaction], int]:
        conditions = ["user_id = $1"]
        params = [user_id]
        param_idx = 2
        
        if transaction_type:
            conditions.append(f"transaction_type = ${param_idx}")
            params.append(transaction_type)
            param_idx += 1
        
        if start_date:
            conditions.append(f"created_at >= ${param_idx}")
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            conditions.append(f"created_at < ${param_idx}")
            params.append(end_date)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        async with self.db_pool.acquire() as conn:
            count_row = await conn.fetchrow(
                f"SELECT COUNT(*) as total FROM point_transactions WHERE {where_clause}", *params
            )
            total = count_row["total"] if count_row else 0
            
            offset = (page - 1) * size
            rows = await conn.fetch(
                f"SELECT * FROM point_transactions WHERE {where_clause} ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}",
                *params, size, offset
            )
            
            transactions = [PointTransaction.from_db_row(dict(row)) for row in rows]
            return transactions, total

    async def checkin(self, user_id: str) -> Dict[str, Any]:
        rule = await self._get_earning_rule("daily_checkin")
        if not rule or not rule.is_active:
            raise ValueError("Daily checkin is not available")
        
        today = date.today()
        async with self.db_pool.acquire() as conn:
            existing = await conn.fetchrow("""
                SELECT COUNT(*) as count FROM point_transactions 
                WHERE user_id = $1 AND source = 'daily_checkin' 
                AND DATE(created_at) = $2
            """, user_id, today)
            
            if existing and existing["count"] > 0:
                raise ValueError("Already checked in today")
            
            consecutive_days = await self._calculate_consecutive_days(conn, user_id)
            
            bonus = 0
            if consecutive_days > 0 and consecutive_days % 7 == 0:
                bonus = rule.points
            
            total_points = rule.points + bonus
            
            tx = await self.add_points(
                user_id, total_points, "daily_checkin",
                f"每日签到 (连续{consecutive_days + 1}天)" + (f" + 周奖励{bonus}" if bonus else "")
            )
            
            return {
                "points_earned": total_points,
                "consecutive_days": consecutive_days + 1,
                "bonus": bonus,
                "transaction": tx.to_dict()
            }

    async def _get_earning_rule(self, action_type: str) -> Optional[EarningRule]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM point_earning_rules WHERE action_type = $1 AND is_active = TRUE",
                action_type
            )
            return EarningRule.from_db_row(dict(row)) if row else None

    async def _calculate_consecutive_days(self, conn, user_id: str) -> int:
        rows = await conn.fetch("""
            SELECT DATE(created_at) as checkin_date 
            FROM point_transactions 
            WHERE user_id = $1 AND source = 'daily_checkin' 
            ORDER BY created_at DESC LIMIT 30
        """, user_id)
        
        if not rows:
            return 0
        
        consecutive = 0
        today = date.today()
        
        for i, row in enumerate(rows):
            expected_date = today - timedelta(days=i + 1)
            if row["checkin_date"] == expected_date:
                consecutive += 1
            else:
                break
        
        return consecutive


from datetime import timedelta

_point_service: Optional[PointService] = None


def get_point_service() -> Optional[PointService]:
    return _point_service


async def init_point_service(db_pool):
    global _point_service
    _point_service = PointService(db_pool)
    return _point_service
