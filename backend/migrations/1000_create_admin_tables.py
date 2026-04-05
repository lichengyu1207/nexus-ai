"""
管理员后台数据库迁移
创建管理员相关表结构
"""
import asyncio
import asyncpg
from datetime import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:147258%40Zxcvbnm@localhost:5432/fangdu"
).replace("postgresql+asyncpg://", "postgresql://")


async def create_admin_tables(conn: asyncpg.Connection):
    """创建管理员相关表"""
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'admin',
            permissions JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            is_superuser BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            created_by UUID,
            login_count INTEGER DEFAULT 0,
            failed_login_count INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            permissions JSONB DEFAULT '{}',
            level INTEGER DEFAULT 0,
            is_system BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            resource VARCHAR(50) NOT NULL,
            action VARCHAR(20) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_role_permissions (
            role_id UUID REFERENCES admin_roles(id) ON DELETE CASCADE,
            permission_id UUID REFERENCES admin_permissions(id) ON DELETE CASCADE,
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            granted_by UUID,
            PRIMARY KEY (role_id, permission_id)
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            admin_id UUID REFERENCES admin_users(id) ON DELETE SET NULL,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(100),
            old_value JSONB,
            new_value JSONB,
            ip_address VARCHAR(45),
            user_agent TEXT,
            request_method VARCHAR(10),
            request_path TEXT,
            request_query TEXT,
            response_status INTEGER,
            duration_ms FLOAT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) UNIQUE NOT NULL,
            refresh_token_hash VARCHAR(255),
            ip_address VARCHAR(45),
            user_agent TEXT,
            device_info JSONB,
            expires_at TIMESTAMP NOT NULL,
            refresh_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_revoked BOOLEAN DEFAULT false
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_configs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key VARCHAR(100) UNIQUE NOT NULL,
            value TEXT,
            value_type VARCHAR(20) DEFAULT 'string',
            description TEXT,
            is_public BOOLEAN DEFAULT false,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by UUID REFERENCES admin_users(id)
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_operations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            admin_id UUID REFERENCES admin_users(id) ON DELETE SET NULL,
            operation_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(100),
            details JSONB,
            status VARCHAR(20) DEFAULT 'pending',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0
        );
    """)
    
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
            type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            data JSONB,
            is_read BOOLEAN DEFAULT false,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
    """)
    
    print("Created admin tables")


async def create_indexes(conn: asyncpg.Connection):
    """创建索引"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);",
        "CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);",
        "CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);",
        "CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active);",
        
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON admin_audit_logs(action);",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_resource ON admin_audit_logs(resource_type, resource_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);",
        
        "CREATE INDEX IF NOT EXISTS idx_admin_sessions_admin_id ON admin_sessions(admin_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_sessions_token_hash ON admin_sessions(token_hash);",
        "CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires_at ON admin_sessions(expires_at);",
        
        "CREATE INDEX IF NOT EXISTS idx_admin_configs_key ON admin_configs(key);",
        
        "CREATE INDEX IF NOT EXISTS idx_admin_operations_admin_id ON admin_operations(admin_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_operations_status ON admin_operations(status);",
        "CREATE INDEX IF NOT EXISTS idx_admin_operations_type ON admin_operations(operation_type);",
        
        "CREATE INDEX IF NOT EXISTS idx_admin_notifications_admin_id ON admin_notifications(admin_id);",
        "CREATE INDEX IF NOT EXISTS idx_admin_notifications_is_read ON admin_notifications(is_read);",
        "CREATE INDEX IF NOT EXISTS idx_admin_notifications_created_at ON admin_notifications(created_at DESC);",
    ]
    
    for idx_sql in indexes:
        await conn.execute(idx_sql)
    
    print(f"Created {len(indexes)} indexes")


async def insert_default_data(conn: asyncpg.Connection):
    """插入默认数据"""
    
    existing_permissions = await conn.fetchval(
        "SELECT COUNT(*) FROM admin_permissions"
    )
    
    if existing_permissions == 0:
        permissions = [
            ("user:read", "查看用户", "user", "read"),
            ("user:create", "创建用户", "user", "create"),
            ("user:update", "更新用户", "user", "update"),
            ("user:delete", "删除用户", "user", "delete"),
            ("agent:read", "查看智能体", "agent", "read"),
            ("agent:update", "更新智能体", "agent", "update"),
            ("agent:execute", "执行智能体操作", "agent", "execute"),
            ("task:read", "查看任务", "task", "read"),
            ("task:execute", "执行任务操作", "task", "execute"),
            ("config:read", "查看配置", "config", "read"),
            ("config:update", "更新配置", "config", "update"),
            ("audit:read", "查看审计日志", "audit", "read"),
            ("stats:read", "查看统计", "stats", "read"),
            ("admin:read", "查看管理员", "admin", "read"),
            ("admin:create", "创建管理员", "admin", "create"),
            ("admin:update", "更新管理员", "admin", "update"),
            ("admin:delete", "删除管理员", "admin", "delete"),
            ("role:read", "查看角色", "role", "read"),
            ("role:manage", "管理角色", "role", "manage"),
        ]
        
        for code, name, resource, action in permissions:
            await conn.execute("""
                INSERT INTO admin_permissions (code, name, resource, action)
                VALUES ($1, $2, $3, $4)
            """, code, name, resource, action)
        
        print(f"Inserted {len(permissions)} permissions")
    
    existing_roles = await conn.fetchval(
        "SELECT COUNT(*) FROM admin_roles"
    )
    
    if existing_roles == 0:
        roles = [
            ("super_admin", "超级管理员", 100, True, [
                "user:read", "user:create", "user:update", "user:delete",
                "agent:read", "agent:update", "agent:execute",
                "task:read", "task:execute",
                "config:read", "config:update",
                "audit:read", "stats:read",
                "admin:read", "admin:create", "admin:update", "admin:delete",
                "role:read", "role:manage"
            ]),
            ("admin", "普通管理员", 50, False, [
                "user:read", "user:update",
                "agent:read",
                "task:read", "task:execute",
                "config:read",
                "audit:read", "stats:read"
            ]),
            ("auditor", "审计员", 30, False, [
                "audit:read", "stats:read"
            ]),
            ("agent_admin", "智能体管理员", 40, False, [
                "agent:read", "agent:update", "agent:execute",
                "task:read", "task:execute",
                "stats:read"
            ]),
        ]
        
        for name, desc, level, is_system, perms in roles:
            role_id = await conn.fetchval("""
                INSERT INTO admin_roles (name, description, level, is_system, permissions)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, name, desc, level, is_system, {"permissions": perms})
            
            for perm_code in perms:
                await conn.execute("""
                    INSERT INTO admin_role_permissions (role_id, permission_id)
                    SELECT $1, id FROM admin_permissions WHERE code = $2
                    ON CONFLICT DO NOTHING
                """, role_id, perm_code)
        
        print(f"Inserted {len(roles)} roles")
    
    existing_admins = await conn.fetchval(
        "SELECT COUNT(*) FROM admin_users WHERE role = 'super_admin'"
    )
    
    if existing_admins == 0:
        import hashlib
        import secrets
        
        password = "Admin@123456"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        await conn.execute("""
            INSERT INTO admin_users (
                username, email, password_hash, role, is_active, is_superuser,
                permissions
            )
            VALUES (
                'superadmin',
                'admin@fangdu.com',
                $1,
                'super_admin',
                true,
                true,
                '{"all": true}'
            )
        """, password_hash)
        
        print("Created default super admin (username: superadmin, password: Admin@123456)")
    
    existing_configs = await conn.fetchval(
        "SELECT COUNT(*) FROM admin_configs"
    )
    
    if existing_configs == 0:
        configs = [
            ("system.name", "房都督平台", "string", "系统名称", True),
            ("system.version", "1.0.0", "string", "系统版本", True),
            ("session.timeout_minutes", "60", "int", "会话超时时间(分钟)", False),
            ("login.max_attempts", "5", "int", "最大登录尝试次数", False),
            ("login.lockout_minutes", "30", "int", "锁定时间(分钟)", False),
            ("audit.retention_days", "90", "int", "审计日志保留天数", False),
            ("notification.email_enabled", "true", "bool", "邮件通知开关", False),
            ("notification.dingtalk_enabled", "false", "bool", "钉钉通知开关", False),
        ]
        
        for key, value, vtype, desc, is_public in configs:
            await conn.execute("""
                INSERT INTO admin_configs (key, value, value_type, description, is_public)
                VALUES ($1, $2, $3, $4, $5)
            """, key, value, vtype, desc, is_public)
        
        print(f"Inserted {len(configs)} default configs")


async def run_migration():
    """运行迁移"""
    print("Starting admin tables migration...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        await create_admin_tables(conn)
        await create_indexes(conn)
        await insert_default_data(conn)
        
        print("Migration completed successfully!")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
