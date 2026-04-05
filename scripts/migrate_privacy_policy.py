"""
隐私政策与用户同意记录系统 - 数据库迁移脚本
创建隐私政策版本表、用户同意记录表
"""
import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-ai.db')

def table_exists(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    return column_name in columns

DEFAULT_PRIVACY_CONTENT = """# 用户隐私政策

**生效日期：{effective_date}**
**版本：1.0**

## 1. 引言

欢迎使用房都督AI房产分析平台（以下简称"本平台"）。我们深知个人信息对您的重要性，并会尽全力保护您的个人信息安全。我们致力于维持您对我们的信任，恪守以下原则，保护您的个人信息：权责一致原则、目的明确原则、选择同意原则、最少够用原则、确保安全原则、主体参与原则、公开透明原则等。

本隐私政策适用于您通过任何方式对本平台服务的访问和使用。请您在使用本平台服务前，仔细阅读并充分理解本隐私政策。

## 2. 我们收集的信息

### 2.1 您主动提供的信息
- **注册信息**：包括您的邮箱地址、用户名、密码等
- **房产信息**：您上传的房产相关数据，包括房产地址、面积、户型等
- **联系方式**：您提供的联系电话、微信等联系方式
- **支付信息**：充值订单相关信息（不包含银行卡号等敏感支付信息）

### 2.2 我们自动收集的信息
- **设备信息**：包括设备型号、操作系统、唯一设备标识符、浏览器类型等
- **日志信息**：包括您使用我们服务时的操作日志、访问时间、访问页面等
- **位置信息**：经过您授权后的地理位置信息（用于提供本地化房产分析服务）
- **Cookie信息**：我们使用Cookie和类似技术来提供、保护和改进我们的服务

## 3. 我们如何使用收集的信息

我们收集的信息将用于以下目的：
- 提供、维护、改进我们的房产分析服务
- 向您发送服务通知、系统更新和安全提醒
- 进行数据分析以改善用户体验和服务质量
- 保护平台安全，防止欺诈和违法行为
- 遵守法律法规的要求

## 4. 信息共享

我们不会向第三方出售、出租或交易您的个人信息。我们仅在以下情况下共享您的信息：
- **获得您的明确同意**：在获得您明确同意后，我们会与第三方共享您的信息
- **法律法规要求**：根据法律法规的要求或政府部门的强制性要求
- **保护权益**：为保护我们、用户或公众的权益、财产或安全
- **业务合作伙伴**：在必要范围内与我们的业务合作伙伴共享（如支付服务提供商），但我们会要求其遵守本隐私政策

## 5. 信息安全

我们采取多种安全措施保护您的个人信息：
- **数据加密**：采用SSL/TLS加密传输，敏感数据加密存储
- **访问控制**：严格的权限管理和身份认证机制
- **安全审计**：定期进行安全审计和漏洞扫描
- **数据备份**：建立完善的数据备份和恢复机制
- **应急响应**：建立个人信息安全事件应急预案

## 6. 您的权利

您对您的个人信息享有以下权利：
- **访问权**：您可以随时访问您的个人信息
- **更正权**：您可以更正不准确的个人信息
- **删除权**：您可以要求删除您的个人信息（在法律法规允许的范围内）
- **撤回同意权**：您可以撤回之前给予的同意
- **注销账户**：您可以申请注销您的账户

## 7. 信息存储

- 您的个人信息存储在中华人民共和国境内的服务器上
- 我们会采取合理措施确保您的个人信息得到安全保护
- 信息保存期限：在您使用本平台服务期间，我们会保留您的个人信息；在您注销账户后，我们会在法律法规规定的期限内删除或匿名化处理您的个人信息

## 8. 未成年人保护

我们非常重视对未成年人个人信息的保护。若您是18周岁以下的未成年人，建议由您的监护人仔细阅读本隐私政策，并在征得您的监护人同意的前提下使用我们的服务。我们不会主动收集未成年人的个人信息。

## 9. 禁止行为

在使用本平台服务时，您不得从事以下行为：
- **虚假注册**：使用虚假身份信息注册账户
- **冒用身份**：冒用他人身份使用本平台服务
- **非法获取**：通过非法手段获取他人个人信息
- **滥用服务**：利用本平台从事欺诈、诈骗等违法活动
- **数据爬取**：未经授权爬取、复制本平台数据
- **恶意攻击**：对本平台进行网络攻击、病毒传播等
- **违规交易**：利用积分系统进行洗钱、套现等违规交易
- **传播违法信息**：通过本平台传播违法、有害信息

如发现上述违规行为，我们有权：
- 立即暂停或终止您的账户
- 删除相关违规内容
- 追究您的法律责任
- 向有关部门举报

## 10. 免责声明

- 本平台提供的房产分析结果仅供参考，不构成投资建议
- 用户应对其上传的房产信息的真实性负责
- 因不可抗力导致的服务中断，本平台不承担责任
- 因用户违规使用导致的损失，本平台不承担责任

## 11. 隐私政策的更新

我们可能会不时更新本隐私政策。更新后的政策将在本平台上公布，并在公布后立即生效。重大变更时，我们会通过平台通知、邮件或其他方式告知您。如您在政策更新后继续使用本服务，即表示您同意接受更新后的隐私政策。

## 12. 联系我们

如果您对本隐私政策有任何疑问、意见或建议，请通过以下方式与我们联系：
- **电子邮件**：lichengyu@fangsuanyun.cn
- **联系电话**：16680508457

我们将在收到您的请求后15个工作日内予以答复。

---

**感谢您对我们的信任！**

**房都督AI团队**
"""

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("隐私政策与用户同意记录系统 - 数据库迁移")
    print("=" * 60)
    
    print("\n1. 创建隐私政策版本表...")
    if not table_exists(cursor, 'privacy_policy_versions'):
        cursor.execute('''
            CREATE TABLE privacy_policy_versions (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                effective_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_privacy_versions_version ON privacy_policy_versions(version)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_privacy_versions_effective ON privacy_policy_versions(effective_date)')
        print("   ✅ privacy_policy_versions 表创建成功")
    else:
        print("   ✅ privacy_policy_versions 表已存在")
    
    print("\n2. 创建用户同意记录表...")
    if not table_exists(cursor, 'user_privacy_agreements'):
        cursor.execute('''
            CREATE TABLE user_privacy_agreements (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                version_id TEXT NOT NULL,
                version TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                agreed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (version_id) REFERENCES privacy_policy_versions(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_agreements_user ON user_privacy_agreements(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_agreements_version ON user_privacy_agreements(version_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_agreements_time ON user_privacy_agreements(agreed_at)')
        print("   ✅ user_privacy_agreements 表创建成功")
    else:
        print("   ✅ user_privacy_agreements 表已存在")
    
    print("\n3. 检查用户表字段...")
    if not column_exists(cursor, 'users', 'agreed_privacy_version'):
        print("   添加 users.agreed_privacy_version 字段...")
        cursor.execute('ALTER TABLE users ADD COLUMN agreed_privacy_version TEXT')
        print("   ✅ 添加成功")
    else:
        print("   ✅ users.agreed_privacy_version 字段已存在")
    
    if not column_exists(cursor, 'users', 'agreed_privacy_at'):
        print("   添加 users.agreed_privacy_at 字段...")
        cursor.execute('ALTER TABLE users ADD COLUMN agreed_privacy_at TIMESTAMP')
        print("   ✅ 添加成功")
    else:
        print("   ✅ users.agreed_privacy_at 字段已存在")
    
    print("\n4. 插入初始隐私政策版本...")
    cursor.execute("SELECT COUNT(*) FROM privacy_policy_versions WHERE version = '1.0'")
    if cursor.fetchone()[0] == 0:
        today = date.today().isoformat()
        content = DEFAULT_PRIVACY_CONTENT.format(effective_date=today)
        cursor.execute('''
            INSERT INTO privacy_policy_versions (id, version, title, content, effective_date, is_current)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', ('privacy-v1', '1.0', '用户隐私政策', content, today))
        print("   ✅ 初始隐私政策版本 1.0 插入成功")
    else:
        print("   ✅ 隐私政策版本 1.0 已存在")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 隐私政策系统迁移完成!")
    print("=" * 60)

if __name__ == '__main__':
    migrate()
