#!/usr/bin/env python3
"""
审计日志验证脚本
验证哈希链完整性和数字签名

用法:
    python scripts/verify_audit_logs.py                    # 验证所有日志
    python scripts/verify_audit_logs.py --limit 1000       # 验证最近1000条
    python scripts/verify_audit_logs.py --sign             # 签名未处理的日志
    python scripts/verify_audit_logs.py --report           # 生成详细报告
    python scripts/verify_audit_logs.py --fix-chain        # 尝试修复链断裂
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.services.audit_verification import (
    audit_verification,
    VerificationStatus,
    VerificationResult
)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str):
    print(f"\n--- {title} ---")


def format_status(status: VerificationStatus) -> str:
    colors = {
        VerificationStatus.VALID: "\033[92m",    # 绿色
        VerificationStatus.WARNING: "\033[93m",  # 黄色
        VerificationStatus.INVALID: "\033[91m",  # 红色
        VerificationStatus.ERROR: "\033[95m",    # 紫色
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    return f"{color}{status.value.upper()}{reset}"


async def verify_logs(
    limit: int = 10000,
    verify_signatures: bool = True,
    verbose: bool = False
) -> VerificationResult:
    print_header("审计日志验证")
    print(f"验证时间: {datetime.utcnow().isoformat()}")
    print(f"最大日志数: {limit}")
    print(f"验证签名: {'是' if verify_signatures else '否'}")
    
    result = await audit_verification.verify_chain(
        limit=limit,
        verify_signatures=verify_signatures
    )
    
    print_section("验证结果")
    print(f"状态: {format_status(result.status)}")
    print(f"总日志数: {result.total_logs}")
    print(f"验证通过: {result.verified_logs}")
    print(f"耗时: {result.duration_ms:.2f}ms")
    
    if result.hash_errors:
        print_section(f"哈希错误 ({len(result.hash_errors)})")
        for err in result.hash_errors[:5]:
            print(f"  - 日志ID: {err['log_id']}")
            print(f"    时间: {err.get('timestamp', 'N/A')}")
            print(f"    预期: {err['expected_hash'][:16]}...")
            print(f"    实际: {err['actual_hash'][:16] if err.get('actual_hash') else 'N/A'}...")
        if len(result.hash_errors) > 5:
            print(f"  ... 还有 {len(result.hash_errors) - 5} 个错误")
    
    if result.chain_errors:
        print_section(f"链断裂 ({len(result.chain_errors)})")
        for err in result.chain_errors[:5]:
            print(f"  - 日志ID: {err['log_id']}")
            print(f"    时间: {err.get('timestamp', 'N/A')}")
            print(f"    预期前哈希: {err['expected_prev_hash'][:16]}...")
            print(f"    实际前哈希: {err['actual_prev_hash'][:16] if err.get('actual_prev_hash') else 'N/A'}...")
        if len(result.chain_errors) > 5:
            print(f"  ... 还有 {len(result.chain_errors) - 5} 个错误")
    
    if result.signature_errors:
        print_section(f"签名错误 ({len(result.signature_errors)})")
        for err in result.signature_errors[:5]:
            print(f"  - 批次ID: {err['batch_id']}")
            print(f"    范围: {err.get('start_log_id', 'N/A')} - {err.get('end_log_id', 'N/A')}")
        if len(result.signature_errors) > 5:
            print(f"  ... 还有 {len(result.signature_errors) - 5} 个错误")
    
    return result


async def sign_logs(batch_size: int = 100) -> int:
    print_header("签名审计日志")
    
    signed_count = await audit_verification.sign_unbatched_logs(batch_size)
    
    if signed_count > 0:
        print(f"成功签名 {signed_count} 条日志")
    else:
        print("没有需要签名的日志")
    
    return signed_count


def generate_report(result: VerificationResult, output_file: Optional[str] = None):
    print_header("生成验证报告")
    
    report = audit_verification.get_verification_report(result)
    
    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report_json)
        print(f"报告已保存到: {output_file}")
    else:
        print(report_json)
    
    return report


def save_verification_record(result: VerificationResult):
    from backend.database import get_db
    import uuid
    
    report = audit_verification.get_verification_report(result)
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO audit_verifications
            (id, verification_time, total_logs, verified_logs, hash_errors,
             chain_errors, signature_errors, status, integrity_score, duration_ms, report)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            result.verification_time,
            result.total_logs,
            result.verified_logs,
            len(result.hash_errors),
            len(result.chain_errors),
            len(result.signature_errors),
            result.status.value,
            report.get("integrity_score", 0),
            result.duration_ms,
            json.dumps(report, ensure_ascii=False)
        ))
        conn.commit()
    
    print(f"验证记录已保存")


async def fix_chain():
    print_header("尝试修复链断裂")
    print("警告: 此操作将重新计算哈希链，仅用于恢复场景")
    
    from backend.database import get_db
    import hashlib
    import json
    
    HASH_KEY = "fangtanai_audit_secret_key_2024"
    
    with get_db() as conn:
        logs = conn.execute("""
            SELECT * FROM audit_logs ORDER BY timestamp ASC
        """).fetchall()
    
    if not logs:
        print("没有日志需要修复")
        return
    
    prev_hash = "0" * 64
    fixed_count = 0
    
    for log in logs:
        log_dict = dict(log)
        
        hash_fields = [
            "timestamp", "user_id", "username", "user_role",
            "ip_address", "user_agent", "action_type", "resource_type",
            "resource_id", "old_value", "new_value", "status",
            "error_message", "prev_hash"
        ]
        
        ordered_data = {}
        for field in hash_fields:
            value = log_dict.get(field)
            if value is not None:
                ordered_data[field] = value
        
        ordered_data["prev_hash"] = prev_hash
        data_str = json.dumps(ordered_data, sort_keys=True, default=str, ensure_ascii=False)
        new_hash = hashlib.sha256((data_str + HASH_KEY).encode("utf-8")).hexdigest()
        
        with get_db() as conn:
            conn.execute("""
                UPDATE audit_logs SET hash = ?, prev_hash = ? WHERE id = ?
            """, (new_hash, prev_hash, log_dict["id"]))
            conn.commit()
        
        prev_hash = new_hash
        fixed_count += 1
    
    print(f"已修复 {fixed_count} 条日志的哈希链")


async def main():
    parser = argparse.ArgumentParser(
        description="审计日志验证工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/verify_audit_logs.py                    # 验证所有日志
  python scripts/verify_audit_logs.py --limit 1000       # 验证最近1000条
  python scripts/verify_audit_logs.py --sign             # 签名未处理的日志
  python scripts/verify_audit_logs.py --report output.json  # 生成报告
  python scripts/verify_audit_logs.py --fix-chain        # 修复链断裂
        """
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10000,
        help="验证的最大日志数 (默认: 10000)"
    )
    
    parser.add_argument(
        "--no-signatures",
        action="store_true",
        help="跳过签名验证"
    )
    
    parser.add_argument(
        "--sign", "-s",
        action="store_true",
        help="签名未处理的日志"
    )
    
    parser.add_argument(
        "--report", "-r",
        type=str,
        default=None,
        help="生成报告并保存到指定文件"
    )
    
    parser.add_argument(
        "--save-record",
        action="store_true",
        help="保存验证记录到数据库"
    )
    
    parser.add_argument(
        "--fix-chain",
        action="store_true",
        help="尝试修复哈希链断裂"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="签名批处理大小 (默认: 100)"
    )
    
    args = parser.parse_args()
    
    if args.fix_chain:
        confirm = input("确定要修复哈希链吗？这将修改日志记录。(y/N): ")
        if confirm.lower() == "y":
            await fix_chain()
        else:
            print("已取消")
        return
    
    if args.sign:
        await sign_logs(args.batch_size)
        return
    
    result = await verify_logs(
        limit=args.limit,
        verify_signatures=not args.no_signatures,
        verbose=args.verbose
    )
    
    if args.report or args.verbose:
        generate_report(result, args.report)
    
    if args.save_record:
        save_verification_record(result)
    
    if result.status == VerificationStatus.INVALID:
        sys.exit(1)
    elif result.status == VerificationStatus.WARNING:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
