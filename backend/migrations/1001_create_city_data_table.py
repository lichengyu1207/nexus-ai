# -*- coding: utf-8 -*-
"""
城市数据表迁移
创建 city_data 表用于存储城市房源数据
"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "1001_create_city_data_table"
down_revision = "1000_create_admin_tables"
branch_labels = None
depends_on = None


def upgrade():
    """创建 city_data 表"""
    op.create_table(
        "city_data",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("city", sa.String(50), nullable=False, index=True),
        sa.Column("avg_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_houses", sa.Integer, nullable=True),
        sa.Column("price_trend", sa.String(20), nullable=True),
        sa.Column("hot_districts", JSONB, nullable=True, server_default="[]"),
        sa.Column("raw_data", JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=True, onupdate=sa.text("NOW()")),
    )
    
    op.create_index("idx_city_data_city", "city_data", ["city"])
    op.create_index("idx_city_data_created", "city_data", ["created_at"])
    op.create_index("idx_city_data_city_created", "city_data", ["city", "created_at"])
    
    op.create_table(
        "city_collection_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("city", sa.String(50), nullable=False, index=True),
        sa.Column("success", sa.Boolean, nullable=False, default=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Float, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    
    op.create_index("idx_collection_log_city", "city_collection_log", ["city"])
    op.create_index("idx_collection_log_timestamp", "city_collection_log", ["timestamp"])


def downgrade():
    """删除 city_data 表"""
    op.drop_index("idx_collection_log_timestamp", "city_collection_log")
    op.drop_index("idx_collection_log_city", "city_collection_log")
    op.drop_table("city_collection_log")
    
    op.drop_index("idx_city_data_city_created", "city_data")
    op.drop_index("idx_city_data_created", "city_data")
    op.drop_index("idx_city_data_city", "city_data")
    op.drop_table("city_data")
