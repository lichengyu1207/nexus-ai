"""
安全扫描工具
检查依赖和代码安全
"""
import os
import subprocess
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from ..logger import get_logger

logger = get_logger("security_scan")


@dataclass
class Vulnerability:
    """漏洞信息"""
    id: str
    name: str
    severity: str
    description: str
    package: str
    installed_version: str
    fixed_version: Optional[str]
    url: Optional[str]


@dataclass
class SecurityFinding:
    """安全发现"""
    file: str
    line: int
    severity: str
    message: str
    confidence: str
    cwe: Optional[str]


class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.results = {
            "vulnerabilities": [],
            "findings": [],
            "scan_time": None,
            "summary": {},
        }
    
    async def scan_dependencies(self) -> List[Vulnerability]:
        """扫描Python依赖漏洞"""
        vulnerabilities = []
        
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.warning(f"Safety check returned non-zero: {result.returncode}")
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for item in data.get("vulnerabilities", []):
                    vuln = Vulnerability(
                        id=item.get("vulnerability_id", "unknown"),
                        name=item.get("package", "unknown"),
                        severity="high",
                        description=item.get("advisory", ""),
                        package=item.get("package", ""),
                        installed_version=item.get("installed_version", ""),
                        fixed_version=item.get("fixed_version"),
                        url=item.get("url"),
                    )
                    vulnerabilities.append(vuln)
        
        except FileNotFoundError:
            logger.warning("safety not installed, skipping dependency scan")
        except Exception as e:
            logger.error(f"Error scanning dependencies: {e}")
        
        return vulnerabilities
    
    async def scan_code(self) -> List[SecurityFinding]:
        """扫描代码安全问题"""
        findings = []
        
        try:
            result = subprocess.run(
                ["bandit", "-r", "backend", "-f", "json"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                for item in data.get("results", []):
                    finding = SecurityFinding(
                        file=item.get("filename", ""),
                        line=item.get("line_number", 0),
                        severity=item.get("issue_severity", "LOW"),
                        message=item.get("issue_text", ""),
                        confidence=item.get("issue_confidence", "MEDIUM"),
                        cwe=item.get("issue_cwe", {}).get("id"),
                    )
                    findings.append(finding)
        
        except FileNotFoundError:
            logger.warning("bandit not installed, skipping code scan")
        except Exception as e:
            logger.error(f"Error scanning code: {e}")
        
        return findings
    
    async def check_secrets(self) -> List[Dict]:
        """检查敏感信息泄露"""
        secrets = []
        
        secret_patterns = [
            ("password", r'password\s*=\s*["\'][^"\']+["\']'),
            ("api_key", r'api_key\s*=\s*["\'][^"\']+["\']'),
            ("secret", r'secret\s*=\s*["\'][^"\']+["\']'),
            ("token", r'token\s*=\s*["\'][^"\']+["\']'),
        ]
        
        import re
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.tsx', '.env')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            for name, pattern in secret_patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    secrets.append({
                                        "file": filepath,
                                        "type": name,
                                        "line": content[:match.start()].count('\n') + 1,
                                        "match": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                                    })
                    except Exception:
                        pass
        
        return secrets
    
    async def run_full_scan(self) -> Dict:
        """运行完整安全扫描"""
        start_time = datetime.now()
        
        logger.info("Starting security scan...")
        
        vulnerabilities = await self.scan_dependencies()
        findings = await self.scan_code()
        secrets = await self.check_secrets()
        
        end_time = datetime.now()
        
        self.results = {
            "vulnerabilities": [v.__dict__ for v in vulnerabilities],
            "findings": [f.__dict__ for f in findings],
            "secrets": secrets,
            "scan_time": (end_time - start_time).total_seconds(),
            "summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "high_severity": len([v for v in vulnerabilities if v.severity == "high"]),
                "total_findings": len(findings),
                "total_secrets": len(secrets),
                "scan_status": "completed",
            }
        }
        
        logger.info(f"Security scan completed: {self.results['summary']}")
        
        return self.results


def generate_security_report(results: Dict) -> str:
    """生成安全报告"""
    report = []
    report.append("# 安全扫描报告")
    report.append(f"\n扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"扫描耗时: {results.get('scan_time', 0):.2f}秒\n")
    
    summary = results.get("summary", {})
    report.append("## 摘要\n")
    report.append(f"- 依赖漏洞: {summary.get('total_vulnerabilities', 0)}")
    report.append(f"- 高危漏洞: {summary.get('high_severity', 0)}")
    report.append(f"- 代码问题: {summary.get('total_findings', 0)}")
    report.append(f"- 敏感信息: {summary.get('total_secrets', 0)}\n")
    
    if results.get("vulnerabilities"):
        report.append("## 依赖漏洞\n")
        for v in results["vulnerabilities"]:
            report.append(f"### {v['package']} ({v['severity']})")
            report.append(f"- ID: {v['id']}")
            report.append(f"- 描述: {v['description']}")
            report.append(f"- 已安装版本: {v['installed_version']}")
            if v['fixed_version']:
                report.append(f"- 修复版本: {v['fixed_version']}")
            report.append("")
    
    if results.get("findings"):
        report.append("## 代码安全问题\n")
        for f in results["findings"][:20]:
            report.append(f"- [{f['severity']}] {f['file']}:{f['line']}")
            report.append(f"  {f['message']}")
        report.append("")
    
    if results.get("secrets"):
        report.append("## 潜在敏感信息\n")
        for s in results["secrets"][:10]:
            report.append(f"- {s['type']} in {s['file']}:{s['line']}")
        report.append("")
    
    return "\n".join(report)


async def run_security_scan():
    """运行安全扫描"""
    scanner = SecurityScanner()
    results = await scanner.run_full_scan()
    return results
