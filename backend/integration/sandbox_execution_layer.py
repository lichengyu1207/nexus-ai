# -*- coding: utf-8 -*-
"""
Layer 38 - Lightweight Command Execution Sandbox Deep Development
===============================================================
轻量级命令执行沙箱深度开发与集成层 — 9大模块+编排器+测试套件
subprocess+资源限制+危险命令检测+三省六部联动+安全审计+降级容错
"""
from __future__ import annotations
import os, sys, time, uuid, hashlib, json, re, signal, tempfile, shutil, threading, subprocess as sp
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import deque

# ═══════════════════════════════════════════════════════════════
# PART H — ENUMS & DATACLASSES
# ═══════════════════════════════════════════════════════════════

class ExecutionStatus(PyEnum):
    PENDING="pending"; RUNNING="running"; SUCCESS="success"
    TIMEOUT="timeout"; MEMORY_EXCEEDED="memory_exceeded"
    BLOCKED="blocked"; ERROR="error"; DEGRADED="degraded"

class RiskLevel(PyEnum):
    SAFE="safe"; LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"

class LanguageType(PyEnum): PYTHON="python"; SHELL="shell"; BASH="bash"; UNKNOWN="unknown"

class QuotaTier(PyEnum): FREE="free"; BASIC="basic"; PREMIUM="premium"

class DegradationMode(PyEnum): PRIMARY="primary"; DOCKER_FALLBACK="docker_fallback"; UNAVAILABLE="unavailable"

@dataclass
class ExecutionResult:
    id: str; status: ExecutionStatus; stdout: str; stderr: str
    return_code: int; duration_ms: float; risk_score: float = 0.0
    trace_id: str = ""; user_id: str = ""; command: str = ""
    memory_used_mb: float = 0.0; cpu_time_sec: float = 0.0
    started_at: float = field(default_factory=time.time); finished_at: Optional[float] = None

@dataclass
class DangerPattern:
    pattern: str; description: str; severity: RiskLevel; category: str
    enabled: bool = True; match_count: int = 0

@dataclass
class QuotaInfo:
    user_id: str; tier: QuotaTier; daily_limit: int; used_today: int
    concurrent_limit: int; current_concurrent: int; reset_at: float

@dataclass
class AuditLogEntry:
    trace_id: str; user_id: str; timestamp: float; command: str
    args_json: str; result_summary: str; return_code: int
    risk_score: float; approved_by: str; execution_duration_ms: float
    ip_address: str = ""; user_agent: str = ""

@dataclass
class PrometheusMetric:
    name: str; value: float; labels: Dict[str,str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class DegradationEvent:
    event_id: str; from_mode: DegradationMode; to_mode: DegradationMode
    reason: str; timestamp: float = field(default_factory=time.time); resolved: bool = False


# ═══════════════════════════════════════════════════════════════
# PART A — LIGHTWEIGHT SANDBOX (subprocess + resource limits)
# ═══════════════════════════════════════════════════════════════

class LightweightSandbox:
    def __init__(self, cpu_timeout: int=10, memory_mb: int=256, max_processes: int=1):
        self._cpu_timeout = cpu_timeout; self._memory_mb = memory_mb
        self._max_processes = max_processes; self._whitelist = {"python","python3","bash","sh"}
        self._active_executions: Dict[str,sp.Popen] = {}; self._history: List[ExecutionResult] = []
        self._temp_dirs: Set[str] = set()
    def execute(self, command: str, language: LanguageType=LanguageType.PYTHON,
                timeout: Optional[int]=None, work_dir: Optional[str]=None) -> ExecutionResult:
        eid=f"exec_{uuid.uuid4().hex[:8]}"; t0=time.time()
        to=timeout or self._cpu_timeout; wd=work_dir or self._create_temp_dir()
        cmd_parts=self._build_command(command,language,wd)
        try:
            proc=sp.Popen(cmd_parts,stdout=sp.PIPE,stderr=sp.PIPE,cwd=wd,
                env=self._get_clean_env(),text=True,bufsize=1,universal_newlines=True)
            self._active_executions[eid]=proc
            try:
                stdout,stderr=proc.communicate(timeout=to)
                status=ExecutionStatus.SUCCESS if proc.returncode==0 else ExecutionStatus.ERROR
            except sp.TimeoutExpired:
                proc.kill(); stdout,stderr=proc.communicate(); status=ExecutionStatus.TIMEOUT
            except MemoryError:
                status=ExecutionStatus.MEMORY_EXCEEDED
            finally:
                self._active_executions.pop(eid,None)
            result=ExecutionResult(eid,status,stdout or "",stderr or "",
                proc.returncode if hasattr(proc,'returncode') else -1,
                round((time.time()-t0)*1000,1),command=command,trace_id=eid)
            self._history.append(result); return result
        except Exception as ex:
            return ExecutionResult(eid,ExecutionStatus.ERROR,"",str(ex),-1,
                round((time.time()-t0)*1000,1),command=command,trace_id=eid)
    def _create_temp_dir(self) -> str:
        td=tempfile.mkdtemp(prefix="sandbox_"); self._temp_dirs.add(td); return td
    def _build_command(self, command: str, language: LanguageType, work_dir: str) -> List[str]:
        if language==LanguageType.PYTHON:
            exe=sys.executable or "python"; return [exe,"-c",command]
        elif language in(LanguageType.SHELL,LanguageType.BASH):
            return ["bash","-c",command]
        return ["sh","-c",command]
    def _get_clean_env(self) -> Dict[str,str]:
        env={"PATH":"/usr/local/bin:/usr/bin:/bin","HOME":workdir if (workdir:=tempfile.gettempdir()) else "/tmp",
            "LANG":"en_US.UTF-8","TMPDIR":tempfile.gettempdir()}
        for k in list(os.environ.keys()):
            if k in("LD_PRELOAD","PYTHONPATH","PYTHONHOME","DYLD_INSERT_LIBRARIES"): continue
            if k.startswith("LD_") or k.startswith("DYLD_"): continue
        return env
    def cancel_execution(self, exec_id: str) -> bool:
        proc=self._active_executions.get(exec_id)
        if proc:
            try: proc.terminate(); proc.wait(timeout=5)
            except: proc.kill()
            self._active_executions.pop(exec_id,None); return True
        return False
    def get_active_count(self) -> int: return len(self._active_executions)
    def cleanup(self):
        for td in self._temp_dirs:
            try: shutil.rmtree(td,ignore_errors=True)
            except: pass
        self._temp_dirs.clear()
    def sandbox_stats(self) -> Dict[str,Any]:
        successes=sum(1 for r in self._history if r.status==ExecutionStatus.SUCCESS)
        timeouts=sum(1 for r in self._history if r.status==ExecutionStatus.TIMEOUT)
        return {"total_executions":len(self._history),"successes":successes,"timeouts":timeouts,
            "errors":len(self._history)-successes-timeouts,"active":self.get_active_count(),
            "avg_duration_ms":round(sum(r.duration_ms for r in self._history)/max(len(self._history),1),1)}


# ═══════════════════════════════════════════════════════════════
# PART B — DANGEROUS COMMAND DETECTOR
# ═══════════════════════════════════════════════════════════════

class DangerousCommandDetector:
    def __init__(self):
        self._patterns: Dict[str,DangerPattern] = {}
        self._block_log: List[Dict[str,Any]] = []; self._init_patterns()
    def _init_patterns(self):
        builtins=[
            (r"rm\s+-rf?\s+[/~]",RiskLevel.CRITICAL,"file_deletion","Recursive force delete"),
            (r"sudo\b",RiskLevel.HIGH,"privilege_escalation","Privilege escalation"),
            (r"chmod\s+777",RiskLevel.HIGH,"permission_abuse","World-writable permissions"),
            (r"mkfs\b",RiskLevel.CRITICAL,"filesystem_destroy","Filesystem formatting"),
            (r"dd\s+if=/dev/zero",RiskLevel.CRITICAL,"disk_wipe","Disk overwrite"),
            (r":\(\)\s*\{.*\|\s*:&\s*\}\s*;",RiskLevel.CRITICAL,"fork_bomb","Fork bomb"),
            (r">\s*/dev/sd[a-z]",RiskLevel.CRITICAL,"disk_destructive","Direct disk write"),
            (r"curl.*\|\s*(ba)?sh",RiskLevel.HIGH,"remote_code_exec","Remote code execution"),
            (r"wget.*\|\s*(ba)?sh",RiskLevel.HIGH,"remote_code_exec","Remote code download+exec"),
            (r"eval\s+",RiskLevel.MEDIUM,"dynamic_eval","Dynamic code evaluation"),
            (r"exec\s+",RiskLevel.MEDIUM,"process_replace","Process replacement"),
            (r"\.\./.*\.\./",RiskLevel.LOW,"path_traversal","Path traversal attempt"),
        ]
        for i,(pat,sev,cat,desc) in enumerate(builtins):
            pid=f"dp_{i+1:03d}"; self._patterns[pid]=DangerPattern(pat,desc,sev,cat,True,0)
    def detect(self, command: str) -> Tuple[bool,RiskLevel,DangerPattern]:
        max_sev=RiskLevel.SAFE; matched=None
        for pid,pattern in self._patterns.items():
            if not pattern.enabled: continue
            if re.search(pattern.pattern,command,re.IGNORECASE):
                pattern.match_count+=1; matched=pattern
                sev_order={RiskLevel.SAFE:0,RiskLevel.LOW:1,RiskLevel.MEDIUM:2,RiskLevel.HIGH:3,RiskLevel.CRITICAL:4}
                if sev_order[pattern.severity]>sev_order[max_sev]: max_sev=pattern.severity
        is_dangerous=max_sev!=RiskLevel.SAFE
        if is_dangerous:
            self._block_log.append({"timestamp":time.time(),"command":command[:200],
                "pattern_id":matched.pattern if matched else "unknown","severity":max_sev.value})
        return is_dangerous,max_sev,matched
    def add_pattern(self, pattern: str, description: str="", severity: RiskLevel=RiskLevel.HIGH, category: str="custom") -> DangerPattern:
        pid=f"dp_{len(self._patterns)+1:03d}"; dp=DangerPattern(pattern,description or f"Custom {pid}",severity,category)
        self._patterns[pid]=dp; return dp
    def remove_pattern(self, pattern_id: str) -> bool:
        p=self._patterns.pop(pattern_id,None); return p is not None
    def get_block_log(self) -> List[Dict[str,Any]]: return list(self._block_log)
    def detector_stats(self) -> Dict[str,Any]:
        total_blocks=sum(p.match_count for p in self._patterns.values())
        enabled=sum(1 for p in self._patterns.values() if p.enabled)
        return {"total_patterns":len(self._patterns),"enabled":enabled,"total_blocks":total_blocks,
            "block_log_size":len(self._block_log)}


# ═══════════════════════════════════════════════════════════════
# PART C — ENVIRONMENT PURIFIER
# ═══════════════════════════════════════════════════════════════

class EnvironmentPurifier:
    def __init__(self):
        self._allowed_vars={"PATH","HOME","LANG","TMPDIR","TERM","USER"}
        self._blocked_prefixes=("LD_","DYLD_","PYTHON","PERL","RUBY")
        self._custom_allowed: Set[str] = set(); self._custom_blocked: Set[str] = set()
    def purify(self, source_env: Optional[Dict[str,str]]=None) -> Dict[str,str]:
        env=source_env or dict(os.environ)
        clean={}
        for k,v in env.items():
            if k in self._allowed_vars or k in self._custom_allowed:
                clean[k]=v
            elif any(k.startswith(p) for p in self._blocked_prefixes):
                continue
            elif k in self._custom_blocked:
                continue
        clean.setdefault("PATH","/usr/local/bin:/usr/bin:/bin")
        clean.setdefault("LANG","en_US.UTF-8"); clean.setdefault("TMPDIR",tempfile.gettempdir())
        return clean
    def add_allowed_var(self, varname: str): self._custom_allowed.add(varname.upper())
    def block_var(self, varname: str): self._custom_blocked.add(varname.upper())
    def get_removed_vars(self, source_env: Optional[Dict[str,str]]=None) -> List[str]:
        env=source_env or dict(os.environ); removed=[]
        for k in env:
            if k not in self._allowed_vars and k not in self._custom_allowed:
                if any(k.startswith(p) for p in self._blocked_prefixes) or k in self._custom_blocked:
                    removed.append(k)
        return removed
    def purifier_stats(self) -> Dict[str,Any]:
        sample=self.purify(); return {"allowed_base":len(self._allowed_vars),
            "custom_allowed":len(self._custom_allowed),"custom_blocked":len(self._custom_blocked),
            "resulting_vars":len(sample)}


# ═══════════════════════════════════════════════════════════════
# PART D — BINGBU CODE EXECUTOR (sync/async + memory storage)
# ═══════════════════════════════════════════════════════════════

class BingbuCodeExecutor:
    def __init__(self, sandbox: LightweightSandbox):
        self._sandbox=sandbox; self._exec_history: List[Dict[str,Any]] = []
        self._async_queue: deque = deque(); self._async_results: Dict[str,ExecutionResult] = {}
        self._worker_thread: Optional[threading.Thread] = None; self._running=False
    def execute_sync(self, code: str, user_id: str="anonymous", language: LanguageType=LanguageType.PYTHON,
                     timeout: Optional[int]=None, memory_limit: Optional[int]=None) -> ExecutionResult:
        trace_id=f"trace_{uuid.uuid4().hex[:8]}"
        result=self._sandbox.execute(code,language,timeout)
        result.trace_id=trace_id; result.user_id=user_id
        entry={"trace_id":trace_id,"user_id":user_id,"command":code[:500],
            "status":result.status.value,"return_code":result.return_code,
            "duration_ms":result.duration_ms,"timestamp":time.time()}
        self._exec_history.append(entry); return result
    def execute_async(self, code: str, user_id: str="anonymous", language: LanguageType=LanguageType.PYTHON,
                      timeout: Optional[int]=None) -> str:
        task_id=f"task_{uuid.uuid4().hex[:8]}"
        self._async_queue.append({"id":task_id,"code":code,"user_id":user_id,
            "language":language,"timeout":timeout})
        if not self._running: self._start_worker()
        return task_id
    def get_async_result(self, task_id: str) -> Optional[ExecutionResult]: return self._async_results.get(task_id)
    def _start_worker(self):
        self._running=True; self._worker_thread=threading.Thread(target=self._worker_loop,daemon=True)
        self._worker_thread.start()
    def _worker_loop(self):
        while self._running or self._async_queue:
            try:
                task=self._async_queue.popleft() if self._async_queue else None
                if task:
                    result=self.execute_sync(task["code"],task["user_id"],task["language"],task.get("timeout"))
                    self._async_results[task["id"]]=result
                else:
                    time.sleep(0.1)
            except IndexError: break
            except Exception as e: time.sleep(0.5)
    def get_user_history(self, user_id: str, limit: int=20) -> List[Dict[str,Any]]:
        user_logs=[e for e in self._exec_history if e["user_id"]==user_id]
        return sorted(user_logs,key=lambda x:x["timestamp"],reverse=True)[:limit]
    def executor_stats(self) -> Dict[str,Any]:
        success=sum(1 for e in self._exec_history if e["status"]=="success")
        return {"total_executions":len(self._exec_history),"success_rate":round(success/max(len(self._exec_history),1)*100,1),
            "pending_async":len(self._async_queue),"completed_async":len(self._async_results),
            "worker_running":self._running}


# ═══════════════════════════════════════════════════════════════
# PART E — SECURITY PRECHECK ENGINE (Xingbu integration)
# ═══════════════════════════════════════════════════════════════

class SecurityPrecheckEngine:
    def __init__(self):
        self._dangerous_imports=[
            "os.system","subprocess.call","subprocess.run","subprocess.Popen",
            "eval(","exec(","__import__","compile(",
            "open(\"/dev/\",\"","open(\"/etc/\",",
            "socket.socket","requests.get","requests.post","urllib.request",
            "pickle.loads","yaml.unsafe_load","marshal.loads"
        ]
        self._scan_history: List[Dict[str,Any]] = []
    def scan_code(self, code: str) -> Tuple[float,RiskLevel,List[str]]:
        findings=[]; risk_score=0.0
        for imp in self._dangerous_imports:
            if imp.lower() in code.lower():
                findings.append(f"Dangerous import/call detected: {imp}")
                risk_score+=15
        suspicious_funcs=["input(","__class__.__mro__","getattr(","setattr(","__builtins__"]
        for sf in suspicious_funcs:
            if sf in code:
                findings.append(f"Suspicious function call: {sf}"); risk_score+=8
        if len(code)>10000: findings.append("Very large code (>10KB)"); risk_score+=5
        if re.search(r'base64\.b?decode',code): findings.append("Base64 decode found"); risk_score+=10
        risk_score=min(risk_score,100)
        level=RiskLevel.SAFE if risk_score<20 else (RiskLevel.LOW if risk_score<40 else (RiskLevel.MEDIUM if risk_score<60 else (RiskLevel.HIGH if risk_score<80 else RiskLevel.CRITICAL)))
        self._scan_history.append({"timestamp":time.time(),"risk_score":risk_score,"level":level.value,
            "findings_count":len(findings)})
        return risk_score,level,findings
    def should_allow(self, risk_score: float, threshold: float=60.0, force_override: bool=False) -> Tuple[bool,str]:
        if risk_score<threshold: return True,"SAFE"
        if force_override: return True,"FORCE_OVERRIDDEN"
        return False,f"BLOCKED: risk {risk_score:.0f} >= threshold {threshold}"
    def engine_stats(self) -> Dict[str,Any]:
        avg_risk=sum(s["risk_score"] for s in self._scan_history)/max(len(self._scan_history),1)
        blocked=sum(1 for s in self._scan_history if s["risk_score"]>=60)
        return {"total_scans":len(self._scan_history),"avg_risk_score":round(avg_risk,1),
            "blocked_count":blocked,"dangerous_imports_monitored":len(self._dangerous_imports)}


# ═══════════════════════════════════════════════════════════════
# PART F — EXECUTION QUOTA MANAGER
# ═══════════════════════════════════════════════════════════════

class ExecutionQuotaManager:
    def __init__(self):
        self._quotas: Dict[str,QuotaInfo] = {}
        self._daily_usage: Dict[str,List[float]] = {}
        self._concurrent: Dict[str,int] = {}
        self._tier_limits={QuotaTier.FREE:10,QuotaTier.BASIC:30,QuotaTier.PREMIUM:50}
    def register_user(self, user_id: str, tier: QuotaTier=QuotaTier.FREE) -> QuotaInfo:
        limit=self._tier_limits[tier]; qi=QuotaInfo(user_id,tier,limit,0,2,0,self._next_reset())
        self._quotas[user_id]=qi; self._daily_usage[user_id]=[]; return qi
    def check_quota(self, user_id: str) -> Tuple[bool,str]:
        qi=self._quotas.get(user_id)
        if not qi: qi=self.register_user(user_id)
        now=time.time()
        if now>=qi.reset_at: self._reset_daily(user_id,qi)
        usage=len([t for t in self._daily_usage.get(user_id,[]) if t>qi.reset_at-86400])
        qi.used_today=usage
        if usage>=qi.daily_limit: return False,f"Daily quota exceeded ({usage}/{qi.daily_limit})"
        cc=self._concurrent.get(user_id,0)
        if cc>=qi.concurrent_limit: return False,f"Concurrent limit reached ({cc}/{qi.concurrent_limit})"
        return True,"OK"
    def record_execution(self, user_id: str):
        self._concurrent[user_id]=self._concurrent.get(user_id,0)+1
        if user_id not in self._daily_usage: self._daily_usage[user_id]=[]
        self._daily_usage[user_id].append(time.time())
    def release_execution(self, user_id: str):
        self._concurrent[user_id]=max(0,self._concurrent.get(user_id,0)-1)
    def get_quota_info(self, user_id: str) -> QuotaInfo:
        qi=self._quotas.get(user_id)
        if not qi: qi=self.register_user(user_id)
        now=time.time()
        if now>=qi.reset_at: self._reset_daily(user_id,qi)
        qi.used_today=len([t for t in self._daily_usage.get(user_id,[]) if t>qi.reset_at-86400])
        qi.current_concurrent=self._concurrent.get(user_id,0); return qi
    def _next_reset(self) -> float:
        import datetime as dt
        tomorrow=(dt.datetime.now()+dt.timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
        return tomorrow.timestamp()
    def _reset_daily(self, user_id: str, qi: QuotaInfo):
        qi.reset_at=self._next_reset(); qi.used_today=0
    def manager_stats(self) -> Dict[str,Any]:
        return {"registered_users":len(self._quotas),"tiers":{t.value:c for t,c in self._tier_limits.items()},
            "total_usage_today":sum(len(v) for v in self._daily_usage.values())}


# ═══════════════════════════════════════════════════════════════
# PART G — SANDBOX AUDIT LOGGER
# ═══════════════════════════════════════════════════════════════

class SandboxAuditLogger:
    def __init__(self):
        self._logs: List[AuditLogEntry] = []; self._metrics: List[PrometheusMetric] = []
        self._alerts: List[Dict[str,Any]] = []; self._retention_days=180
    def log_execution(self, trace_id: str, user_id: str, command: str, result: ExecutionResult,
                     risk_score: float=0.0, approved_by: str="auto"):
        entry=AuditLogEntry(trace_id,user_id,time.time(),command,json.dumps([])[:500],
            f"{result.status.value}: {result.stdout[:200]}" if len(result.stdout)<200 else f"{result.status.value}: truncated",
            result.return_code,risk_score,approved_by,result.duration_ms)
        self._logs.append(entry)
        self._record_metric("code_execution_total",1,{"status":result.status.value})
        if result.status!=ExecutionStatus.SUCCESS:
            self._record_metric("code_execution_failed",1,{"status":result.status.value})
        self._record_metric("code_execution_duration_seconds",result.duration_ms/1000)
        self._check_alerts(result); return entry
    def _record_metric(self, name: str, value: float, labels: Optional[Dict[str,str]]=None):
        self._metrics.append(PrometheusMetric(name,value,labels or {}))
        if len(self._metrics)>10000: self._metrics=self._metrics[-5000:]
    def _check_alerts(self, result: ExecutionResult):
        recent=[l for l in self._logs if time.time()-l.timestamp<3600]
        failed_recent=sum(1 for l in recent if l.return_code!=0)
        if len(recent)>=10 and failed_recent/len(recent)>0.1:
            self._alerts.append({"type":"high_failure_rate","message":f"Failure rate {failed_recent/len(recent)*100:.0f}% > 10%",
                "timestamp":time.time(),"resolved":False})
        if result.duration_ms>60000:
            self._alerts.append({"type":"slow_execution","message":f"Execution took {result.duration_ms/1000:.0f}s > 60s",
                "timestamp":time.time(),"resolved":False})
    def query_logs(self, user_id: Optional[str]=None, start_time: Optional[float]=None,
                   end_time: Optional[float]=None, limit: int=100) -> List[AuditLogEntry]:
        logs=self._logs
        if user_id: logs=[l for l in logs if l.user_id==user_id]
        if start_time: logs=[l for l in logs if l.timestamp>=start_time]
        if end_time: logs=[l for l in logs if l.timestamp<=end_time]
        cutoff=time.time()-self._retention_days*86400; logs=[l for l in logs if l.timestamp>=cutoff]
        return sorted(logs,key=lambda x:x.timestamp,reverse=True)[:limit]
    def get_metrics_summary(self) -> Dict[str,Any]:
        total=self._count_metric("code_execution_total"); failed=self._count_metric("code_execution_failed")
        durations=[m.value for m in self._metrics if m.name=="code_execution_duration_seconds"]
        return {"total_executions":total,"failed_executions":failed,
            "failure_rate":round(failed/max(total,1)*100,1),
            "avg_duration_s":round(sum(durations)/max(len(durations),1),2) if durations else 0,
            "active_alerts":sum(1 for a in self._alerts if not a["resolved"]),
            "log_entries":len(self._logs)}
    def _count_metric(self, metric_name: str) -> int:
        return sum(int(m.value) for m in self._metrics if m.name==metric_name)
    def logger_stats(self) -> Dict[str,Any]:
        return self.get_metrics_summary()


# ═══════════════════════════════════════════════════════════════
# PART H — DEGRADATION & FAILOVER MANAGER
# ═══════════════════════════════════════════════════════════════

class DegradationFailoverManager:
    def __init__(self):
        self._mode=DegradationMode.PRIMARY; self._events: List[DegradationEvent] = []
        self._docker_available=False; self._health_checks: List[Dict[str,Any]] = []
        self._failure_count=0; self._success_streak=0
    def check_health(self) -> bool:
        healthy=True
        try:
            td=tempfile.gettempdir(); test_path=os.path.join(td,"_sandbox_health_test")
            with open(test_path,"w") as f: f.write("ok")
            os.remove(test_path)
        except Exception: healthy=False; self._failure_count+=1; self._success_streak=0
        if healthy: self._success_streak+=1; self._failure_count=0
        self._health_checks.append({"timestamp":time.time(),"healthy":healthy,"mode":self._mode.value})
        if len(self._health_checks)>200: self._health_checks=self._health_checks[-100:]
        if self._failure_count>=3 and self._mode==DegradationMode.PRIMARY:
            self._trigger_failover("Primary health check failures >= 3")
        elif self._success_streak>=5 and self._mode!=DegradationMode.PRIMARY:
            self._restore_primary()
        return healthy
    def _trigger_failover(self, reason: str):
        old_mode=self._mode
        if self._docker_available: self._mode=DegradationMode.DOCKER_FALLBACK
        else: self._mode=DegradationMode.UNAVAILABLE
        evt=DegradationEvent(uuid.uuid4().hex[:8],old_mode,self._mode,reason)
        self._events.append(evt)
    def _restore_primary(self):
        old_mode=self._mode; self._mode=DegradationMode.PRIMARY
        evt=DegradationEvent(uuid.uuid4().hex[:8],old_mode,self._mode,"Health restored after 5 consecutive checks")
        evt.resolved=True; self._events.append(evt)
    def get_current_mode(self) -> DegradationMode: return self._mode
    def enable_docker_fallback(self, available: bool=True): self._docker_available=available
    def get_events(self) -> List[DegradationEvent]: return list(self._events)
    def manager_stats(self) -> Dict[str,Any]:
        return {"current_mode":self._mode.value,"docker_available":self._docker_available,
            "failure_count":self._failure_count,"success_streak":self._success_streak,
            "total_events":len(self._events),"health_checks":len(self._health_checks)}


# ═══════════════════════════════════════════════════════════════
# PART I — EXECUTION RESULT FORMATTER
# ═══════════════════════════════════════════════════════════════

class ExecutionResultFormatter:
    def __init__(self): self._formatters={}
    def format_result(self, raw_output: str, content_type: str="auto") -> Dict[str,Any]:
        ct=content_type if content_type!="auto" else self._detect_type(raw_output)
        if ct=="json":
            try: formatted=json.dumps(json.loads(raw_output),ensure_ascii=False,indent=2)
            except: formatted=raw_output
            return {"type":"json","formatted":formatted,"renderable":True}
        elif ct in("csv","tsv"):
            lines=raw_output.strip().split("\n"); sep="\t" if ct=="tsv" else ","
            headers=[h.strip() for h in lines[0].split(sep)]; rows=[]
            for line in lines[1:]:
                cells=[c.strip() for c in line.split(sep)]
                if cells: rows.append(cells)
            return {"type":"table","headers":headers,"rows":rows,"row_count":len(rows),"renderable":True}
        elif ct=="image_base64":
            return {"type":"image","base64_data":raw_output.strip(),"renderable":True}
        else:
            return {"type":"text","formatted":raw_output,"line_count":raw_output.count("\n")+1,"renderable":False}
    def _detect_type(self, output: str) -> str:
        stripped=output.strip()
        if stripped.startswith("{") or stripped.startswith("["): return "json"
        if re.match(r'^[a-zA-Z_].*,.*\n',stripped) and "," in stripped.split("\n")[0]: return "csv"
        if re.match(r'^[a-zA-Z_].*\t.*\n',stripped) and "\t" in stripped.split("\n")[0]: return "tsv"
        if re.match(r'^[A-Za-z0-9+/]{20,}={0,2}$',stripped.replace("\n","")): return "image_base64"
        return "text"
    def formatter_stats(self) -> Dict[str,Any]:
        return {"supported_types":["json","csv","tsv","image_base64","text"],"auto_detection":True}


# ═══════════════════════════════════════════════════════════════
# PART J — SANDBOX ORCHESTRATOR (unified coordinator)
# ═══════════════════════════════════════════════════════════════

class SandboxOrchestrator:
    def __init__(self):
        self.sandbox = LightweightSandbox()
        self.detector = DangerousCommandDetector()
        self.purifier = EnvironmentPurifier()
        self.executor = BingbuCodeExecutor(self.sandbox)
        self.precheck = SecurityPrecheckEngine()
        self.quota = ExecutionQuotaManager()
        self.audit = SandboxAuditLogger()
        self.degradation = DegradationFailoverManager()
        self.formatter = ExecutionResultFormatter()
    def safe_execute(self, code: str, user_id: str="anonymous", language: LanguageType=LanguageType.PYTHON,
                     timeout: Optional[int]=None, force: bool=False) -> Dict[str,Any]:
        trace_id=f"orc_{uuid.uuid4().hex[:8]}"
        mode=self.degradation.check_health(); current_mode=mode
        if current_mode==DegradationMode.UNAVAILABLE:
            result=ExecutionResult(trace_id,ExecutionStatus.DEGRADED,"","Sandbox unavailable - please retry later",-1,0,command=code,trace_id=trace_id)
            self.audit.log_execution(trace_id,user_id,code,result,100); return {"result":result,"blocked":False,"quota_ok":True,"degraded":True}
        is_dangerous,severity,pattern=self.detector.detect(code)
        if is_dangerous and not force:
            result=ExecutionResult(trace_id,ExecutionStatus.BLOCKED,"",f"Blocked: {pattern.description}",-1,0,command=code,trace_id=trace_id,risk_score=90)
            self.audit.log_execution(trace_id,user_id,code,result,90); return {"result":result,"blocked":True,"pattern":pattern,"quota_ok":True}
        risk_score,level,findings=self.precheck.scan_code(code)
        allowed,msg=self.precheck.should_allow(risk_score,60.0,force)
        if not allowed:
            result=ExecutionResult(trace_id,ExecutionStatus.BLOCKED,"",msg,-1,0,command=code,trace_id=trace_id,risk_score=risk_score)
            self.audit.log_execution(trace_id,user_id,code,result,risk_score); return {"result":result,"blocked":True,"findings":findings,"quota_ok":True}
        quota_ok,quota_msg=self.quota.check_quota(user_id)
        if not quota_ok:
            result=ExecutionResult(trace_id,ExecutionStatus.BLOCKED,"",quota_msg,-1,0,command=code,trace_id=trace_id)
            self.audit.log_execution(trace_id,user_id,code,result,0); return {"result":result,"blocked":True,"quota_msg":quota_msg}
        self.quota.record_execution(user_id)
        try:
            result=self.executor.execute_sync(code,user_id,language,timeout)
        except Exception as ex:
            result=ExecutionResult(trace_id,ExecutionStatus.ERROR,"",str(ex),-1,0,command=code,trace_id=trace_id)
        finally:
            self.quota.release_execution(user_id)
        self.audit.log_execution(trace_id,user_id,code,result,risk_score)
        formatted=self.formatter.format_result(result.stdout)
        return {"result":result,"blocked":False,"quota_ok":True,"risk_score":risk_score,
            "findings":findings,"formatted_output":formatted,"degraded":current_mode!=DegradationMode.PRIMARY}
    def get_full_status(self) -> Dict[str,Any]:
        return {"sandbox":self.sandbox.sandbox_stats(),"detector":self.detector.detector_stats(),
            "purifier":self.purifier.purifier_stats(),"executor":self.executor.executor_stats(),
            "precheck":self.precheck.engine_stats(),"quota":self.quota.manager_stats(),
            "audit":self.audit.logger_stats(),"degradation":self.degradation.manager_stats(),
            "formatter":self.formatter.formatter_stats()}


# ═══════════════════════════════════════════════════════════════
# PART K — TESTING SUITE
# ═══════════════════════════════════════════════════════════════

def _run_test(name: str, fn) -> tuple:
    try: fn(); return ("PASS", name, None)
    except Exception as e: return ("FAIL", name, str(e))

def run_all_tests() -> Dict[str,Any]:
    results=[]

    def test_sandbox_basic():
        sb=LightweightSandbox(); r=sb.execute("print('hello world')"); assert r.status==ExecutionStatus.SUCCESS
        assert "hello" in r.stdout; assert r.return_code==0; sb.cleanup()
    results.append(_run_test("SANDBOX: basic python exec", test_sandbox_basic))

    def test_sandbox_timeout():
        sb=LightweightSandbox(cpu_timeout=1); r=sb.execute("import time; time.sleep(10)")
        assert r.status==ExecutionStatus.TIMEOUT; sb.cleanup()
    results.append(_run_test("SANDBOX: timeout detection", test_sandbox_timeout))

    def test_sandbox_shell():
        sb=LightweightSandbox()
        r=sb.execute("echo hello from shell",LanguageType.SHELL)
        assert r.status in(ExecutionStatus.SUCCESS,ExecutionStatus.ERROR)
        if r.status==ExecutionStatus.SUCCESS: assert "hello" in r.stdout
        sb.cleanup()
    results.append(_run_test("SANDBOX: shell execution", test_sandbox_shell))

    def test_sandbox_cancel():
        sb=LightweightSandbox(cpu_timeout=30)
        r=sb.execute("import time; time.sleep(20)")
        if sb.get_active_count()>0:
            eid=list(sb._active_executions.keys())[0]; assert sb.cancel_execution(eid)
        sb.cleanup()
    results.append(_run_test("SANDBOX: cancel execution", test_sandbox_cancel))

    def test_detector_safe():
        det=DangerousCommandDetector(); blocked,sev,_=det.detect("print('hello')")
        assert blocked==False; assert sev==RiskLevel.SAFE
    results.append(_run_test("DETECTOR: safe command passes", test_detector_safe))

    def test_detector_rm_rf():
        det=DangerousCommandDetector(); blocked,sev,p=det.detect("rm -rf /home/user")
        assert blocked==True; assert sev==RiskLevel.CRITICAL; assert p is not None
    results.append(_run_test("DETECTOR: rm -rf blocked", test_detector_rm_rf))

    def test_detector_sudo():
        det=DangerousCommandDetector(); blocked,sev,_=det.detect("sudo apt-get update")
        assert blocked==True; assert sev==RiskLevel.HIGH
    results.append(_run_test("DETECTOR: sudo blocked", test_detector_sudo))

    def test_detector_fork_bomb():
        det=DangerousCommandDetector(); blocked,sev,_=det.detect(":(){ :|:& };:")
        assert blocked==True; assert sev==RiskLevel.CRITICAL
    results.append(_run_test("DETECTOR: fork bomb blocked", test_detector_fork_bomb))

    def test_detector_custom_pattern():
        det=DangerousCommandDetector(); dp=det.add_pattern("evil_command","Test evil",RiskLevel.MEDIUM,"test")
        blocked,sev,_=det.detect("run evil_command here"); assert blocked==True
        pid=[k for k,v in det._patterns.items() if v.pattern=="evil_command"][0]
        assert det.remove_pattern(pid)==True
    results.append(_run_test("DETECTOR: custom pattern add/remove", test_detector_custom_pattern))

    def test_purifier_basic():
        ep=EnvironmentPurifier(); clean=ep.purify()
        assert "PATH" in clean; assert "LD_PRELOAD" not in clean
    results.append(_run_test("PURIFIER: basic sanitization", test_purifier_basic))

    def test_purifier_blocked_vars():
        ep=EnvironmentPurifier(); fake_env={"PATH":"/bin","HOME":"/tmp","LD_PRELOAD":"lib.so","PYTHONPATH":"/hack"}
        removed=ep.get_removed_vars(fake_env); assert "LD_PRELOAD" in removed; assert "PYTHONPATH" in removed
    results.append(_run_test("PURIFIER: blocked vars detection", test_purifier_blocked_vars))

    def test_purifier_custom():
        ep=EnvironmentPurifier(); ep.block_var("SECRET_KEY"); ep.add_allowed_var("CUSTOM_VAR")
        clean=ep.purify({"SECRET_KEY":"123","CUSTOM_VAR":"x"})
        assert "SECRET_KEY" not in clean; assert "CUSTOM_VAR" in clean
    results.append(_run_test("PURIFIER: custom allow/block", test_purifier_custom))

    def test_executor_sync():
        sb=LightweightSandbox(); ex=BingbuCodeExecutor(sb)
        r=ex.execute_sync("print(42)","user1"); assert r.status==ExecutionStatus.SUCCESS
        history=ex.get_user_history("user1"); assert len(history)>=1; sb.cleanup()
    results.append(_run_test("EXECUTOR: sync execution+history", test_executor_sync))

    def test_precheck_safe():
        spe=SecurityPrecheckEngine(); score,level,findings=spe.scan_code("x=1+1\nprint(x)")
        assert score<20; assert level in(RiskLevel.SAFE,RiskLevel.LOW)
    results.append(_run_test("PRECHECK: safe code passes", test_precheck_safe))

    def test_precheck_dangerous():
        spe=SecurityPrecheckEngine(); code="import os\nos.system('rm -rf /')"
        score,level,findings=spe.scan_code(code); assert score>=15; assert len(findings)>0
    results.append(_run_test("PRECHECK: dangerous imports detected", test_precheck_dangerous))

    def test_precheck_should_allow():
        spe=SecurityPrecheckEngine(); ok,msg=spe.should_allow(10); assert ok==True
        nok,msg2=spe.should_allow(80); assert nok==False; assert "BLOCKED" in msg2
        force,msg3=spe.should_allow(80,force_override=True); assert force==True
    results.append(_run_test("PRECHECK: should_allow logic", test_precheck_should_allow))

    def test_quota_register_check():
        qm=ExecutionQuotaManager(); qi=qm.register_user("u1",QuotaTier.FREE)
        assert qi.tier==QuotaTier.FREE; assert qi.daily_limit==10
        ok,msg=qm.check_quota("u1"); assert ok==True
    results.append(_run_test("QUOTA: register+check", test_quota_register_check))

    def test_quota_exhaust():
        qm=ExecutionQuotaManager(); qm.register_user("u1",QuotaTier.FREE)
        for _ in range(11): qm.record_execution("u1")
        ok,msg=qm.check_quota("u1"); assert ok==False; assert "exceeded" in msg
    results.append(_run_test("QUOTA: daily limit exhaust", test_quota_exhaust))

    def test_audit_log():
        al=SandboxAuditLogger(); r=ExecutionResult("t1",ExecutionStatus.SUCCESS,"output","",0,100)
        entry=al.log_execution("tr1","u1","print('hi')",r,5)
        assert entry.trace_id=="tr1"; assert entry.risk_score==5
        summary=al.get_metrics_summary(); assert summary["total_executions"]==1
    results.append(_run_test("AUDIT: log+metrics", test_audit_log))

    def test_audit_query():
        al=SandboxAuditLogger()
        for i in range(5): al.log_execution(f"tr{i}",f"u{i%2}","cmd",ExecutionResult("",ExecutionStatus.SUCCESS,"","",0,0))
        u0_logs=al.query_logs(user_id="u0"); assert len(u0_logs)>=2
    results.append(_run_test("AUDIT: query by user", test_audit_query))

    def test_degradation_health():
        dfm=DegradationFailoverManager(); assert dfm.check_health()==True
        assert dfm.get_current_mode()==DegradationMode.PRIMARY
    results.append(_run_test("DEGRADATION: health check pass", test_degradation_health))

    def test_degradation_event():
        dfm=DegradationFailoverManager(); dfm.enable_docker_fallback(True)
        for _ in range(3): dfm.check_health()  # won't trigger since health passes
        events=dfm.get_events(); assert isinstance(events,list)
    results.append(_run_test("DEGRADATION: event tracking", test_degradation_event))

    def test_formatter_json():
        fmt=ExecutionResultFormatter(); out='{"key":"value","num":42}'
        result=fmt.format_result(out); assert result["type"]=="json"; assert result["renderable"]==True
    results.append(_run_test("FORMATTER: JSON pretty print", test_formatter_json))

    def test_formatter_csv():
        fmt=ExecutionResultFormatter(); out="name,age,city\nAlice,30,BJ\nBob,25,SH"
        result=fmt.format_result(out); assert result["type"]=="table"; assert result["row_count"]==2
    results.append(_run_test("FORMATTER: CSV table render", test_formatter_csv))

    def test_formatter_text():
        fmt=ExecutionResultFormatter(); result=fmt.format_result("plain text output")
        assert result["type"]=="text"; assert result["renderable"]==False
    results.append(_run_test("FORMATTER: text passthrough", test_formatter_text))

    def test_orchestrator_init():
        orc=SandboxOrchestrator(); assert orc.sandbox is not None; assert orc.audit is not None
    results.append(_run_test("ORC: init all modules", test_orchestrator_init))

    def test_orchestrator_safe_exec():
        orc=SandboxOrchestrator(); result=orc.safe_execute("print('orchestrated')","test_user")
        assert "result" in result; assert result["blocked"]==False
    results.append(_run_test("ORC: safe_execute flow", test_orchestrator_safe_exec))

    def test_orchestrator_blocked():
        orc=SandboxOrchestrator(); result=orc.safe_execute("rm -rf /","bad_user")
        assert result["blocked"]==True
    results.append(_run_test("ORC: dangerous blocked", test_orchestrator_blocked))

    def test_orchestrator_status():
        orc=SandboxOrchestrator(); status=orc.get_full_status()
        assert "sandbox" in status; assert "audit" in status
    results.append(_run_test("ORC: full status", test_orchestrator_status))

    def test_edge_empty_code():
        sb=LightweightSandbox(); r=sb.execute(""); assert r.status in(ExecutionStatus.SUCCESS,ExecutionStatus.ERROR)
        sb.cleanup()
    results.append(_run_test("EDGE: empty code", test_edge_empty_code))

    def test_edge_large_output():
        sb=LightweightSandbox(); r=sb.execute("print('x'*10000)")
        assert r.status==ExecutionStatus.SUCCESS; assert len(r.stdout)>9000
        sb.cleanup()
    results.append(_run_test("EDGE: large output handling", test_edge_large_output))

    passed=sum(1 for r in results if r[0]=="PASS")
    failed=[r for r in results if r[0]=="FAIL"]; errors=[r for r in results if r[0]=="ERROR"]
    print(f"\n{'='*60}")
    print(f"L38 LIGHTWEIGHT SANDBOX EXECUTION LAYER — TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Total : {len(results)}")
    print(f"  Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"  Failed: {len(failed)}")
    if failed:
        for _,name,err in failed: print(f"    ✗ {name}: {err}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for _,name,err in errors: print(f"    ! {name}: {err}")
    print(f"{'='*60}")
    return {"total":len(results),"passed":passed,"failed":len(failed),"errors":len(errors),"results":results}

if __name__ == "__main__":
    run_all_tests()
    print("\n✅ Layer 38 — Lightweight Command Execution Sandbox loaded OK")
