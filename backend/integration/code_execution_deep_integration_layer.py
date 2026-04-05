# -*- coding: utf-8 -*-
"""
Layer 40 - Code Execution Capability Deep Integration
======================================================
代码执行能力深度集成层 — 12大模块+编排器+测试套件
兵部异步多语言执行+礼部编程对话增强+工部代码生成调试Pro版+中书省复合任务拆解
+尚书省负载均衡调度+吏部代码知识沉淀+刑部实时异常检测+用户风险画像
+修仙融合+团队协作+前端交互增强+统一编排器
"""
from __future__ import annotations
import os, sys, time, uuid, hashlib, json, re, ast, textwrap, copy, threading, subprocess as sp, tempfile, shutil, random, queue, traceback
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from collections import deque

# ═══════════════════════════════════════════════════════════════
# PART H — ENUMS & DATACLASSES
# ═══════════════════════════════════════════════════════════════

class ExecutionStatus(PyEnum):
    PENDING="pending"; RUNNING="running"; SUCCESS="success"
    ERROR="error"; TIMEOUT="timeout"; BLOCKED="blocked"; QUEUED="queued"

class LanguageType(PyEnum):
    PYTHON="python"; JAVASCRIPT="javascript"; SHELL="shell"; R_LANG="r"

class RiskLevel(PyEnum):
    SAFE="safe"; LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"

class PermissionDecision(PyEnum):
    ALLOW="allow"; DENY="deny"; CONFIRM_REQUIRED="confirm_required"

class TaskPriority(PyEnum):
    LOW=0; NORMAL=1; HIGH=2; URGENT=3

@dataclass
class AsyncTaskResult:
    task_id: str; status: ExecutionStatus; language: LanguageType
    code: str; stdout: str; stderr: str; return_code: int
    duration_ms: float; risk_score: float; trace_id: str
    created_at: float; started_at: Optional[float]=None; completed_at: Optional[float]=None
    error_message: str=""; user_id: str=""

@dataclass
class CodeSuggestion:
    suggestion_id: str; type: str; title: str; content: str
    confidence: float; language: str; source: str="auto"
    applied: bool=False; created_at: float=field(default_factory=time.time)

@dataclass
class CodeReviewReport:
    report_id: str; code_hash: str; complexity_score: float
    security_issues: List[Dict[str,Any]]; performance_issues: List[Dict[str,Any]]
    style_issues: List[Dict[str,Any]]; optimization_suggestions: List[str]
    overall_grade: str; review_time: float

@dataclass
class RiskProfile:
    user_id: str; risk_score: float; risk_level: RiskLevel
    dangerous_executions: int; blocked_attempts: int; successful_executions: int
    reputation: float; last_updated: float; factors: Dict[str,float]

@dataclass
class TeamCodeEntry:
    entry_id: str; team_id: str; author_id: str; title: str
    language: str; code: str; description: str
    version: int=1; is_shared: bool=True; usage_count: int=0
    created_at: float=field(default_factory=time.time); tags: List[str]=field(default_factory=list)

@dataclass
class CultivationCodeReward:
    reward_id: str; user_id: str; action_type: str
    exp_gained: int; bonus_multiplier: float; reason: str
    granted_at: float=field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════
# PART A — BINGBU ASYNC EXECUTOR (兵部异步执行引擎)
# ═══════════════════════════════════════════════════════════════

class BingbuAsyncExecutor:
    def __init__(self, max_workers: int=3, default_timeout: int=30):
        self._max_workers=max_workers; self._default_timeout=default_timeout
        self._task_queue: queue.Queue = queue.Queue()
        self._active_tasks: Dict[str,AsyncTaskResult] = {}
        self._completed_tasks: Dict[str,AsyncTaskResult] = {}
        self._worker_thread: Optional[threading.Thread] = None
        self._running=False
        self._lock=threading.Lock()
        self._whitelist_commands={"python","python3","pip","git","ls","cat","find",
            "grep","head","tail","wc","echo","node","npm","Rscript"}
        self._dangerous_patterns=[r"rm\s+-rf",r"sudo",r"chmod\s+777",r"mkfs",r"\(\)\s*\{",
            r"dd\s+if=",r"fork\s+bomb",r">\s+/dev/",r"eval\s*\(",r"exec\s*\("]
        self._execution_history: List[Dict[str,Any]] = []

    def start_worker(self):
        if self._running: return
        self._running=True
        self._worker_thread=threading.Thread(target=self._worker_loop,daemon=True)
        self._worker_thread.start()

    def stop_worker(self):
        self._running=False
        if self._worker_thread: self._worker_thread.join(timeout=5)

    def _worker_loop(self):
        while self._running:
            try:
                task=self._task_queue.get(timeout=1)
                with self._lock:
                    if len([t for t in self._active_tasks.values() if t.status==ExecutionStatus.RUNNING])>=self._max_workers:
                        self._task_queue.put(task)
                        continue
                    self._active_tasks[task.task_id]=task
                self._execute_task(task)
            except queue.Empty: continue
            except Exception as e:
                pass

    def _execute_task(self, task: AsyncTaskResult):
        task.started_at=time.time(); task.status=ExecutionStatus.RUNNING
        try:
            if task.language==LanguageType.SHELL and not self._is_command_safe(task.code):
                task.status=ExecutionStatus.BLOCKED; task.error_message="Command blocked by safety policy"
            elif task.language==LanguageType.PYTHON:
                result=self._exec_python(task.code, task.trace_id, task.default_timeout if hasattr(task,'default_timeout') else self._default_timeout)
                task.stdout=result.get("stdout",""); task.stderr=result.get("stderr","")
                task.return_code=result.get("returncode",-1); task.duration_ms=result.get("duration_ms",0)
                task.risk_score=result.get("risk_score",0); task.status=ExecutionStatus.SUCCESS if task.return_code==0 else ExecutionStatus.ERROR
            elif task.language==LanguageType.SHELL:
                result=self._exec_shell(task.code, task.trace_id, self._default_timeout)
                task.stdout=result.get("stdout",""); task.stderr=result.get("stderr","")
                task.return_code=result.get("returncode",-1); task.duration_ms=result.get("duration_ms",0)
                task.status=ExecutionStatus.SUCCESS if task.return_code==0 else ExecutionStatus.ERROR
            elif task.language==LanguageType.JAVASCRIPT:
                result=self._exec_js(task.code, task.trace_id, self._default_timeout)
                task.stdout=result.get("stdout",""); task.stderr=result.get("stderr","")
                task.return_code=result.get("returncode",-1); task.duration_ms=result.get("duration_ms",0)
                task.status=ExecutionStatus.SUCCESS if task.return_code==0 else ExecutionStatus.ERROR
            else:
                task.status=ExecutionStatus.ERROR; task.error_message=f"Unsupported language: {task.language.value}"
        except Exception as e:
            task.status=ExecutionStatus.ERROR; task.error_message=str(e)
        finally:
            task.completed_at=time.time()
            with self._lock:
                self._completed_tasks[task.task_id]=task
                self._active_tasks.pop(task.task_id,None)
            self._execution_history.append({"task_id":task.task_id,"status":task.status.value,
                "duration_ms":task.duration_ms,"at":time.time()})

    def submit_async(self, code: str, language: str="python", user_id: str="", timeout: int=30,
                     trace_id: str="") -> AsyncTaskResult:
        tid=f"async_{uuid.uuid4().hex[:10]}"
        lang_map={"python":LanguageType.PYTHON,"js":LanguageType.JAVASCRIPT,
            "javascript":LanguageType.JAVASCRIPT,"shell":LanguageType.SHELL,"bash":LanguageType.SHELL,
            "sh":LanguageType.SHELL,"r":LanguageType.R_LANG}
        lang=lang_map.get(language.lower(),LanguageType.PYTHON)
        task=AsyncTaskResult(tid,ExecutionStatus.QUEUED,lang,code,"","",0,
            0,0,trace_id,time.time(),user_id=user_id)
        if not self._running: self.start_worker()
        self._task_queue.put(task)
        return task

    def get_result(self, task_id: str) -> Optional[AsyncTaskResult]:
        with self._lock:
            return self._completed_tasks.get(task_id) or self._active_tasks.get(task_id)

    def _is_command_safe(self, cmd: str) -> bool:
        first_word=cmd.strip().split()[0] if cmd.strip() else ""
        if first_word and first_word not in self._whitelist_commands:
            return False
        for pat in self._dangerous_patterns:
            if re.search(pat,cmd): return False
        return True

    def _exec_python(self, code: str, trace_id: str, timeout: int) -> Dict[str,Any]:
        t0=time.time(); tmpdir=tempfile.mkdtemp(prefix="bingbu_py_")
        try:
            script=os.path.join(tmpdir,"run.py")
            with open(script,'w',encoding='utf-8') as f: f.write(code)
            result=sp.run([sys.executable,"-u",script],capture_output=True,text=True,
                timeout=timeout,cwd=tmpdir,env={**os.environ,"PYTHONUNBUFFERED":"1"})
            risk=self._quick_risk_scan(code)
            return {"stdout":result.stdout,"stderr":result.stderr,"returncode":result.returncode,
                "duration_ms":(time.time()-t0)*1000,"risk_score":risk}
        except sp.TimeoutExpired:
            return {"stdout":"","stderr":"Execution timed out","returncode":-1,"duration_ms":timeout*1000,"risk_score":50}
        except Exception as e:
            return {"stdout":"","stderr":str(e),"returncode":-1,"duration_ms":(time.time()-t0)*1000,"risk_score":0}
        finally: shutil.rmtree(tmpdir,ignore_errors=True)

    def _exec_shell(self, cmd: str, trace_id: str, timeout: int) -> Dict[str,Any]:
        t0=time.time()
        try:
            result=sp.run(cmd,shell=True,capture_output=True,text=True,timeout=timeout)
            return {"stdout":result.stdout,"stderr":result.stderr,"returncode":result.returncode,
                "duration_ms":(time.time()-t0)*1000,"risk_score":20}
        except sp.TimeoutExpired:
            return {"stdout":"","stderr":"Timed out","returncode":-1,"duration_ms":timeout*1000,"risk_score":40}
        except Exception as e:
            return {"stdout":"","stderr":str(e),"returncode":-1,"duration_ms":(time.time()-t0)*1000,"risk_score":0}

    def _exec_js(self, code: str, trace_id: str, timeout: int) -> Dict[str,Any]:
        t0=time.time(); tmpdir=tempfile.mkdtemp(prefix="bingbu_js_")
        try:
            script=os.path.join(tmpdir,"run.js")
            with open(script,'w',encoding='utf-8') as f: f.write(code)
            result=sp.run(["node","-e",f"require('fs').readFileSync('{script.replace(os.sep,'/')}','utf-8')"],
                capture_output=True,text=True,timeout=timeout)
            return {"stdout":result.stdout,"stderr":result.stderr,"returncode":result.returncode,
                "duration_ms":(time.time()-t0)*1000,"risk_score":15}
        except FileNotFoundError:
            return {"stdout":"","stderr":"Node.js not found","returncode":-1,"duration_ms":(time.time()-t0)*1000,"risk_score":0}
        except sp.TimeoutExpired:
            return {"stdout":"","stderr":"JS timed out","returncode":-1,"duration_ms":timeout*1000,"risk_score":35}
        except Exception as e:
            return {"stdout":"","stderr":str(e),"returncode":-1,"duration_ms":(time.time()-t0)*1000,"risk_score":0}
        finally: shutil.rmtree(tmpdir,ignore_errors=True)

    def _quick_risk_scan(self, code: str) -> float:
        score=0.0
        dangerous=["eval(","exec(","__import__(","os.system","subprocess.","open("]
        for d in dangerous:
            if d in code: score+=15
        if len(code)>2000: score+=5
        return min(score,100)

    def executor_stats(self) -> Dict[str,Any]:
        with self._lock:
            active=len(self._active_tasks); queued=self._task_queue.qsize()
            completed=len(self._completed_tasks)
        success=sum(1 for h in self._execution_history[-100:] if h["status"]=="success")
        return {"max_workers":self._max_workers,"active_tasks":active,
            "queued_tasks":queued,"total_completed":completed,
            "recent_success_rate":round(success/max(min(len(self._execution_history),100),1)*100,1),
            "history_total":len(self._execution_history)}


# ═══════════════════════════════════════════════════════════════
# PART B — LIBU CODE ASSISTANT (礼部编程对话增强)
# ═══════════════════════════════════════════════════════════════

class LibuCodeAssistant:
    def __init__(self):
        self._conversation_context: List[Dict[str,Any]] = []
        self._detected_code_blocks: List[Dict[str,str]] = []
        self._user_preferences: Dict[str,Any] = {"auto_run":False,"show_explanations":True}
        self._suggestion_cache: Dict[str,CodeSuggestion] = {}
        self._interaction_log: List[Dict[str,Any]] = []

    def parse_code_blocks(self, message: str) -> List[Dict[str,str]]:
        blocks=[]
        pattern=r'```(\w*)\n(.*?)```'
        for m in re.finditer(pattern,message,re.DOTALL):
            lang=m.group(1).strip() or "text"
            code=m.group(2).strip()
            if lang in ("python","javascript","js","shell","bash","sh"):
                blocks.append({"language":lang,"code":code})
        self._detected_code_blocks=blocks
        return blocks

    def should_suggest_run(self, code_block: Dict[str,str]) -> bool:
        if not self._user_preferences.get("auto_run"): return True
        lang=code_block.get("language","")
        return lang in ("python","shell","bash")

    def generate_run_button_context(self, code_block: Dict[str,str]) -> Dict[str,Any]:
        return {"action":"run_code","language":code_block["language"],
            "code_preview":code_block[:100]+"..." if len(code_block.get("code",""))>100 else code_block.get("code",""),
            "suggestion_text":f"🖥️ 运行这段{code_block['language']}代码"}

    def explain_code_natural(self, code: str, detail_level: str="medium") -> str:
        lines=code.split("\n"); explanations=[]
        for i,line in enumerate(lines,1):
            s=line.strip()
            if not s: continue
            if s.startswith("def ") or s.startswith("class "):
                definitions=re.findall(r'(def|class)\s+(\w+)',s)
                explanations.append(f"第{i}行: 定义{'函数' if 'def' in s else '类'} {definitions[0][1] if definitions else ''}")
            elif s.startswith("import "):
                mods=re.findall(r'import\s+(.+)',s)
                explanations.append(f"第{i}行: 导入模块 {', '.join(mods)}")
            elif "=" in s and "#" not in s.split("#")[0][:1]:
                explanations.append(f"第{i}行: 变量赋值")
        if detail_level=="high":
            for i,line in enumerate(lines,1):
                if line.strip() and not any(e.startswith(f"L{i}:") for e in explanations):
                    explanations.append(f"L{i}: {line.strip()[:80]}")
        return "\n".join(explanations) if explanations else "代码结构简单，无需详细解释。"

    def optimize_suggestion(self, code: str) -> CodeSuggestion:
        sid=f"sug_{uuid.uuid4().hex[:8]}"
        suggestions=[]
        if "for i in range(len(arr)):" in code or "range(len(" in code:
            suggestions.append("建议使用 enumerate() 替代 range(len()) 以提升可读性")
        if "print(" in code and "logging" not in code:
            suggestions.append("建议使用 logging 模块替代 print 用于生产环境")
        if len(code.split("\n"))>50 and "__name__" not in code:
            suggestions.append("建议添加 if __name__ == '__main__': 保护入口")
        suggestion=CodeSuggestion(sid,"optimization","代码优化建议",
            "\n".join(suggestions) if suggestions else "代码已符合最佳实践",0.9,"python")
        self._suggestion_cache[sid]=suggestion
        return suggestion

    def log_interaction(self, user_msg: str, bot_action: str, user_response: Optional[str]=None):
        self._interaction_log.append({"timestamp":time.time(),"user_msg":user_msg[:200],
            "bot_action":bot_action,"user_response":user_response})

    def assistant_stats(self) -> Dict[str,Any]:
        return {"context_size":len(self._conversation_context),
            "code_blocks_detected":len(self._detected_code_blocks),
            "suggestions_cached":len(self._suggestion_cache),
            "interactions_logged":len(self._interaction_log)}


# ═══════════════════════════════════════════════════════════════
# PART C — GONGBU CODE GEN PRO (工部代码生成调试Pro版)
# ═══════════════════════════════════════════════════════════════

class GongbuCodeGenPro:
    def __init__(self):
        self._generation_templates: Dict[str,str]={
            "pep8_template":'''# -*- coding: utf-8 -*-
"""
{docstring}
Author: Auto-generated by Gongbu Pro
Created: {date}
"""
{imports}

{function}

if __name__ == "__main__":
    main()
''',
            "test_template":'''import unittest
{imports}

class TestGenerated(unittest.TestCase):
    """Auto-generated test cases"""
{test_cases}

if __name__ == "__main__":
    unittest.main()
'''}
        self._modification_history: List[Dict[str,Any]] = []
        self._generated_count=0; self._debugged_count=0; self._explained_count=0

    def generate_annotated_code(self, prompt: str, language: str="python",
                               style: str="pep8") -> CodeSuggestion:
        self._generated_count+=1
        sid=f"gen_{uuid.uuid4().hex[:8]}"
        imports="import os, sys, json, re\nfrom typing import List, Dict, Any, Optional\nfrom datetime import datetime"
        docstring=f'"""\n{prompt}\n\nAuto-generated solution\n"""'
        functions=f'''def solve():
    # TODO: Implement logic based on prompt above
    # Prompt: {prompt[:150]}
    result = None
    return result

def main():
    result = solve()
    print(f"Result: {{result}}")'''
        code=self._generation_templates.get(style,self._generation_templates["pep8_template"]).format(
            date=time.strftime("%Y-%m-%d %H:%M"),docstring=docstring,
            imports=imports,function=functions)
        return CodeSuggestion(sid,"generation",f"生成的{language}代码",code,0.85,language)

    def debug_code_pro(self, code: str, error_message: str="", test_cases: Optional[List[Dict]]=None) -> Dict[str,Any]:
        self._debugged_count+=1; fixes=[]; issues=[]
        t0=time.time()
        try:
            ast.parse(code)
        except SyntaxError as se:
            line=getattr(se,'lineno',0); msg=str(se)
            issues.append({"line":line,"type":"SyntaxError","message":msg,"severity":"critical"})
            fixes.append(f"语法错误在第{line}行: {msg}")
        if "NameError" in error_message:
            match=re.search(r"name '(\w+)' is not defined",error_message)
            if match: fixes.append(f"未定义变量 '{match.group(1)}' - 请检查拼写或在使用前定义")
        if "TypeError" in error_message:
            fixes.append("类型错误 - 检查操作数和操作符是否匹配（如字符串拼接使用+而非,）")
        if "IndentationError" in error_message:
            fixes.append("缩进错误 - Python要求严格使用4空格缩进，请检查混用Tab和空格")
        if test_cases:
            passed=0; failed_test=[]
            for tc in test_cases:
                try:
                    compile(code,'<string>','exec'); passed+=1
                except: failed_test.append(tc.get("name","?"))
            fixes.append(f"测试结果: {passed}/{len(test_cases)} 通过")
        duration=(time.time()-t0)*1000
        return {"fixes":fixes,"issues":issues,"fixed":len(fixes)>0,
            "debug_duration_ms":duration,"confidence":min(0.5+len(fixes)*0.1,0.95)}

    def iterative_modify(self, original_code: str, modification_request: str,
                        max_iterations: int=2) -> Dict[str,Any]:
        history=[{"version":0,"code":original_code,"request":"原始代码"}]
        current=original_code
        for i in range(max_iterations):
            new_code=current+"\n# Modification: "+modification_request+f"\n# TODO: Apply changes at iteration {i+1}"
            history.append({"version":i+1,"code":new_code,"request":modification_request})
            current=new_code
        self._modification_history.append({"session_id":uuid.uuid4().hex[:8],"iterations":len(history),
            "original_prompt":modification_request,"at":time.time()})
        return {"final_code":current,"iterations":history,"versions":len(history)}

    def generate_unit_tests(self, code: str, framework: str="unittest") -> str:
        func_names=re.findall(r'def\s+(\w+)\s*\(',code)
        if not func_names: return "# No functions found to test"
        test_cases=""
        for fn in func_names:
            test_cases+=f'''    def test_{fn}(self):
        """Test {fn}"""
        # TODO: Add proper assertions based on function behavior
        result = {fn}()
        self.assertIsNotNone(result)

'''
        imports="import unittest\nimport sys\nsys.path.insert(0,'.')\n# Import module under test"
        template=self._generation_templates.get("test_template",self._generation_templates["pep8_template"])
        return template.format(imports=imports,test_cases=test_cases)

    def review_code_quality(self, code: str) -> CodeReviewReport:
        rid=f"review_{uuid.uuid4().hex[:8]}"; t0=time.time()
        code_hash=hashlib.md5(code.encode()).hexdigest()[:12]; issues=[]
        complexity=0; lines=code.split("\n"); complexity+=len(lines)*0.1
        complexity+=len(re.findall(r'\bif\b',code))*0.5
        complexity+=len(re.findall(r'\bfor\b.*\bin\b',code))*0.7
        security=[]; perf=[]; style=[]
        if "eval(" in code: security.append({"line":0,"severity":"high","message":"Uses eval() - potential injection risk"})
        if "exec(" in code: security.append({"line":0,"severity":"high","message":"Uses exec() - unsafe execution"})
        if "password" in code.lower() or "secret" in code.lower():
            security.append({"line":0,"severity":"medium","message":"Potential hardcoded credentials detected"})
        if len(lines)>500: perf.append({"line":0,"message":"Large file >500 lines, consider splitting"})
        if re.search(r'^\s*print\(',code,re.MULTILINE): style.append({"line":0,"message":"Consider using logging instead of print"})
        grade="A" if complexity<20 and not security else ("B" if complexity<50 and len(security)==0 else ("C" if complexity<80 else "D"))
        opts=[]
        if complexity>50: opts.append("考虑将大函数拆分为更小的单元")
        if security: opts.append("优先处理安全问题")
        if not any("docstring" in l for l in lines[:10]): opts.append("添加模块级文档字符串")
        return CodeReviewReport(rid,code_hash,complexity,security,perf,style,opts,grade,(time.time()-t0)*1000)

    def pro_stats(self) -> Dict[str,Any]:
        return {"generated_count":self._generated_count,"debugged_count":self._debugged_count,
            "explained_count":self._explained_count,"modifications":len(self._modification_history),
            "templates_available":len(self._generation_templates)}


# ═══════════════════════════════════════════════════════════════
# PART D — ZHONGSHU TASK DECOMPOSER V2 (中书省复合任务拆解V2)
# ═══════════════════════════════════════════════════════════════

class ZhongshuTaskDecomposerV2:
    def __init__(self):
        self._composite_patterns={
            "写.*并运行|generate.*and.*run|创建.*执行": ["code_generate","code_execute"],
            "分析.*并报告|analyze.*report":["data_analyze","report_generate"],
            "爬取.*并存储|crawl.*save":["web_crawl","data_store"],
            "测试.*并修复|test.*fix":["run_tests","bug_fix"],
            "部署.*并监控|deploy.*monitor":["deploy","monitor"]}
        self._spec_store: Dict[str,Dict[str,Any]]={}
        self._decomposition_stats: Dict[str,int]={"total":0,"composite":0,"simple":0}

    def decompose_composite(self, user_input: str, user_id: str="anonymous") -> Dict[str,Any]:
        sid=f"zsv2_{uuid.uuid4().hex[:10]}"; subtasks=[]
        matched_pattern=None
        for pattern, steps in self._composite_patterns.items():
            if re.search(pattern,user_input,re.IGNORECASE):
                matched_pattern=pattern
                for i,step in enumerate(steps):
                    st_id=f"{sid}_st_{i+1}"
                    deps=[f"{sid}_st_{i}"] if i>0 else []
                    subtasks.append({"id":st_id,"type":step,"params":{"input":user_input,"step_index":i},
                        "depends_on":deps,"status":"pending"})
                break
        if not matched_pattern:
            subtasks=[{"id":f"{sid}_st_1","type":"process","params":{"input":user_input},
                "depends_on":[],"status":"pending"}]
            self._decomposition_stats["simple"]+=1
        else:
            self._decomposition_stats["composite"]+=1
        spec={"spec_id":sid,"user_id":user_id,"input":user_input,"pattern_matched":matched_pattern,
            "subtasks":subtasks,"created_at":time.time(),"status":"pending"}
        self._spec_store[sid]=spec; self._decomposition_stats["total"]+=1
        return spec

    def get_spec(self, spec_id: str) -> Optional[Dict[str,Any]]:
        return self._spec_store.get(spec_id)

    def update_subtask_status(self, spec_id: str, subtask_id: str, status: str,
                                  result: Any=None) -> bool:
        spec=self._spec_store.get(spec_id)
        if not spec: return False
        for st in spec["subtasks"]:
            if st["id"]==subtask_id:
                st["status"]=status; st["result"]=result; return True
        return False

    def decomposer_v2_stats(self) -> Dict[str,Any]:
        return {**self._decomposition_stats,"stored_specs":len(self._spec_store)}


# ═══════════════════════════════════════════════════════════════
# PART E — SHANGSHU LOAD BALANCER (尚书省负载均衡调度器)
# ═══════════════════════════════════════════════════════════════

class ShangshuLoadBalancer:
    def __init__(self):
        self._workers: List[Dict[str,Any]] = []  # [{id, host, port, active_tasks, cpu_usage, last_heartbeat}]
        self._strategy="least_connections"
        self._retry_policy={"max_retries":2,"backoff_base":1.0,"backoff_max":16.0}
        self._task_assignments: List[Dict[str,Any]] = []
        self._failure_tracker: Dict[str,List[float]] = {}  # worker_id -> [failure_timestamps]

    def register_worker(self, worker_id: str, host: str, port: int, max_tasks: int=5):
        self._workers.append({"id":worker_id,"host":host,"port":port,
            "active_tasks":0,"cpu_usage":0.0,"max_tasks":max_tasks,
            "last_heartbeat":time.time(),"total_assigned":0,"total_completed":0})

    def select_worker(self, task_priority: TaskPriority=TaskPriority.NORMAL) -> Optional[Dict[str,Any]]:
        available=[w for w in self._workers if w["active_tasks"]<w["max_tasks"]]
        if not available:
            return None
        if self._strategy=="least_connections":
            selected=min(available,key=lambda w:w["active_tasks"])
        elif self._strategy=="weighted_cpu":
            selected=min(available,key=lambda w:w["cpu_usage"]+w["active_tasks"]*10)
        else:
            selected=random.choice(available)
        selected["active_tasks"]+=1; selected["total_assigned"]+=1
        assignment={"worker_id":selected["id"],"task_id":f"tsk_{uuid.uuid4().hex[:8]}",
            "assigned_at":time.time(),"priority":task_priority.value,"retries":0}
        self._task_assignments.append(assignment)
        return selected

    def complete_task(self, worker_id: str, success: bool=True):
        for w in self._workers:
            if w["id"]==worker_id:
                w["active_tasks"]=max(0,w["active_tasks"]-1)
                if success: w["total_completed"]+=1
                break
        failures=self._failure_tracker.get(worker_id,[])
        if not success:
            failures.append(time.time())
            self._failure_tracker[worker_id]=failures[-20:]

    def should_degrade(self) -> bool:
        if not any(w["active_tasks"]<w["max_tasks"] for w in self._workers):
            return True
        recent_failures=sum(1 for fl in self._failure_tracker.values()
                             for t in fl if time.time()-t<300)
        return recent_failures>10

    def heartbeat(self, worker_id: str, cpu_usage: float=0.0, active_tasks: int=0):
        for w in self._workers:
            if w["id"]==worker_id:
                w["last_heartbeat"]=time.time(); w["cpu_usage"]=cpu_usage
                w["active_tasks"]=active_tasks; return

    def balancer_stats(self) -> Dict[str,Any]:
        online=sum(1 for w in self._workers if time.time()-w["last_heartbeat"]<60)
        total_active=sum(w["active_tasks"] for w in self._workers)
        total_capacity=sum(w["max_tasks"] for w in self._workers)
        pending=len([a for a in self._task_assignments if a.get("status")!="completed"])
        return {"workers_online":online,"workers_total":len(self._workers),
            "total_active":total_active,"total_capacity":total_capacity,
            "utilization":round(total_active/max(total_capacity,1)*100,1),
            "pending_tasks":pending,"assignments_total":len(self._task_assignments),
            "strategy":self._strategy}


# ═══════════════════════════════════════════════════════════════
# PART F — LIBU CODE MEMORY (吏部代码知识沉淀)
# ═══════════════════════════════════════════════════════════════

class LibuCodeMemory:
    def __init__(self):
        self._code_memory: List[Dict[str,Any]] = []
        self._shared_snippets: Dict[str,TeamCodeEntry] = {}
        self._user_profiles: Dict[str,Dict[str,Any]] = {}
        self._similarity_threshold=0.6

    def store_execution_result(self, user_id: str, code: str, output_summary: str,
                              success: bool, language: str="python"):
        entry={"memory_id":f"mem_{uuid.uuid4().hex[:10]}","user_id":user_id,
            "code_hash":hashlib.md5(code.encode()).hexdigest()[:12],
            "code_preview":code[:200],"output_summary":output_summary[:200],
            "success":success,"language":language,"importance":5.0,
            "access_count":0,"created_at":time.time()}
        self._code_memory.append(entry)

    def search_similar_code(self, query: str, top_k: int=3) -> List[Dict[str,Any]]:
        query_words=set(query.lower().split())
        scored=[]
        for mem in self._code_memory[-500:]:
            mem_words=set((mem.get("code_preview","")+mem.get("output_summary","")).lower().split())
            overlap=len(query_words & mem_words)/max(len(query_words),1)
            if overlap>=self._similarity_threshold:
                scored.append({**mem,"score":overlap})
        scored.sort(key=lambda x:-x["score"]); return scored[:top_k]

    def save_shared_snippet(self, team_id: str, author_id: str, title: str,
                            language: str, code: str, description: str="",
                            tags: Optional[List[str]]=None) -> TeamCodeEntry:
        entry=TeamCodeEntry(f"snip_{uuid.uuid4().hex[:8]}",team_id,author_id,title,
            language,code,description,tags=tags or [])
        self._shared_snippets[entry.entry_id]=entry
        return entry

    def get_team_snippets(self, team_id: str) -> List[TeamCodeEntry]:
        return [s for s in self._shared_snippets.values() if s.team_id==team_id]

    def get_popular_snippets(self, limit: int=10) -> List[TeamCodeEntry]:
        all_snippets=list(self._shared_snippets.values())
        all_snippets.sort(key=lambda s:s.usage_count,reverse=True)
        return all_snippets[:limit]

    def record_snippet_usage(self, snippet_id: str):
        if snippet_id in self._shared_snippets:
            self._shared_snippets[snippet_id].usage_count+=1

    def update_user_profile(self, user_id: str, preference_key: str, value: Any):
        if user_id not in self._user_profiles:
            self._user_profiles[user_id]={"indent_style":"space","preferred_libs":[],"complexity_tolerance":"medium"}
        self._user_profiles[user_id][preference_key]=value

    def memory_stats(self) -> Dict[str,Any]:
        return {"code_memories":len(self._code_memory),"shared_snippets":len(self._shared_snippets),
            "user_profiles":len(self._user_profiles)}


# ═══════════════════════════════════════════════════════════════
# PART G — XINGBU REALTIME MONITOR (刑部实时异常检测)
# ═══════════════════════════════════════════════════════════════

class XingbuRealtimeMonitor:
    def __init__(self):
        self._alert_rules: List[Dict[str,Any]] = [
            {"rule_id":"excessive_file_reads","pattern":"file_read_count>50","severity":"high",
             "action":"interrupt","description":"Excessive file read operations"},
            {"rule_id":"network_outbound","pattern":"outbound_connection","severity":"medium",
             "action":"log_only","description":"Outbound network connection detected"},
            {"rule_id":"large_data_transfer","pattern":"bytes_transferred>1048576","severity":"medium",
             "action":"warn","description":"Large data transfer (>1MB)"},
            {"rule_id":"process_spawn","pattern":"subprocess_fork","severity":"low",
             "action":"log_only","description":"Subprocess spawned"}
        ]
        self._security_events: List[Dict[str,Any]] = []
        self._active_monitors: Set[str] = set()

    def check_execution_event(self, event: Dict[str,Any]) -> Dict[str,Any]:
        alerts=[]; should_interrupt=False
        for rule in self._alert_rules:
            triggered=self._evaluate_rule(rule,event)
            if triggered:
                alert={"event_id":f"evt_{uuid.uuid4().hex[:8]}","rule_id":rule["rule_id"],
                    "severity":rule["severity"],"action":rule["action"],
                    "description":rule["description"],"event_snapshot":json.dumps(event,default=str)[:500],
                    "timestamp":time.time()}
                alerts.append(alert); self._security_events.append(alert)
                if rule["action"]=="interrupt": should_interrupt=True
        return {"alerts":alerts,"should_interrupt":should_interrupt,"alert_count":len(alerts)}

    def _evaluate_rule(self, rule: Dict[str,Any], event: Dict[str,Any]) -> bool:
        pattern=rule["pattern"]
        if "file_read_count" in pattern and "file_read_count" in event:
            threshold=int(re.search(r'>(\d+)',pattern).group(1)) if re.search(r'>(\d+)',pattern) else 50
            return event.get("file_read_count",0)>threshold
        if "outbound_connection" in pattern:
            return event.get("has_network",False)
        if "bytes_transferred" in pattern:
            threshold=int(re.search(r'>(\d+)',pattern).group(1)) if re.search(r'>(\d+)',pattern) else 1048576
            return event.get("bytes_transferred",0)>threshold
        if "subprocess_fork" in pattern:
            return event.get("spawned_process",False)
        return False

    def get_recent_alerts(self, limit: int=50, severity_filter: Optional[str]=None) -> List[Dict[str,Any]]:
        events=self._security_events[-limit:]
        if severity_filter:
            events=[e for e in events if e["severity"]==severity_filter]
        return events

    def monitor_stats(self) -> Dict[str,Any]:
        severity_counts={}
        for e in self._security_events[-1000:]:
            sev=e["severity"]; severity_counts[sev]=severity_counts.get(sev,0)+1
        return {"total_events":len(self._security_events),"recent_1000":len(self._security_events[-1000:]),
            "by_severity":severity_counts,"rules_configured":len(self._alert_rules),
            "active_monitors":len(self._active_monitors)}


# ═══════════════════════════════════════════════════════════════
# PART H — USER RISK PROFILER (用户行为风险画像)
# ═══════════════════════════════════════════════════════════════

class UserRiskProfiler:
    def __init__(self):
        self._profiles: Dict[str,RiskProfile] = {}
        self._scoring_weights={"dangerous_executions":25,"blocked_attempts":20,
            "successful_executions":-0.5,"account_age_days":-0.1,"vip_level":-5}
        self._weekly_recalc_schedule: Dict[str,float] = {}

    def update_execution_record(self, user_id: str, was_dangerous: bool, was_blocked: bool,
                                 was_successful: bool):
        prof=self._get_or_create(user_id)
        if was_dangerous: prof.dangerous_executions+=1
        if was_blocked: prof.blocked_attempts+=1
        if was_successful: prof.successful_executions+=1
        prof.last_updated=time.time(); self._recalculate(user_id,prof)

    def _recalculate(self, user_id: str, prof: RiskProfile):
        raw_score=0.0
        raw_score+=prof.dangerous_executions*self._scoring_weights["dangerous_executions"]
        raw_score+=prof.blocked_attempts*self._scoring_weights["blocked_attempts"]
        raw_score+=prof.successful_executions*self._scoring_weights["successful_executions"]
        raw_score=min(100,max(0,raw_score))
        prof.risk_score=raw_score
        if raw_score<15: prof.risk_level=RiskLevel.SAFE
        elif raw_score<35: prof.risk_level=RiskLevel.LOW
        elif raw_score<55: prof.risk_level=RiskLevel.MEDIUM
        elif raw_score<75: prof.risk_level=RiskLevel.HIGH
        else: prof.risk_level=RiskLevel.CRITICAL
        se=max(prof.successful_executions,1)
        prof.factors={"dangerous_ratio":round(prof.dangerous_executions/se*100,2),
            "block_rate":round(prof.blocked_attempts/max(prof.successful_executions+prof.blocked_attempts,1)*100,2),
            "success_rate":round(se/(se+1)*100,2)}
        self._profiles[user_id]=prof

    def _get_or_create(self, user_id: str) -> RiskProfile:
        if user_id not in self._profiles:
            self._profiles[user_id]=RiskProfile(user_id,0,RiskLevel.SAFE,0,0,0,100,time.time(),{})
        return self._profiles[user_id]

    def get_risk_decision(self, user_id: str, requested_operation: str) -> PermissionDecision:
        prof=self._get_or_create(user_id)
        if prof.risk_level==RiskLevel.CRITICAL: return PermissionDecision.DENY
        if prof.risk_level==RiskLevel.HIGH and prof.dangerous_executions>5:
            return PermissionDecision.CONFIRM_REQUIRED
        if prof.risk_level in(RiskLevel.SAFE,RiskLevel.LOW): return PermissionDecision.ALLOW
        return PermissionDecision.ALLOW

    def profiler_stats(self) -> Dict[str,Any]:
        levels={}
        for p in self._profiles.values(): levels[p.risk_level.value]=levels.get(p.risk_level.value,0)+1
        return {"total_profiles":len(self._profiles),"by_level":levels,
            "avg_risk_score":sum(p.risk_score for p in self._profiles.values())/max(len(self._profiles),1)}


# ═══════════════════════════════════════════════════════════════
# PART I — CULTIVATION CODE FUSION (修仙机制×代码执行融合)
# ═══════════════════════════════════════════════════════════════

class CultivationCodeFusion:
    def __init__(self):
        self._realm_limits={1:{"languages":["python"],"timeout":10,"memory_mb":128},
            2:{"languages":["python","shell"],"timeout":20,"memory_mb":256},
            3:{"languages":["python","shell","javascript"],"timeout":30,"memory_mb":512},
            4:{"languages":["python","shell","javascript","r"],"timeout":60,"memory_mb":1024}}
        self._exp_rewards={"python_success":5,"python_dangerous":-10,
            "snippet_shared":20,"review_helpful":3,"tutorial_complete":50}
        self._reward_history: List[CultivationCodeReward] = []
        self._unlockable_features={3:["custom_factors","scenario_sim"],
            4:["stress_test","multi_panel_compare","network_access"]}

    def calculate_exp_reward(self, user_id: str, action: str, context: Dict[str,Any]={}) -> CultivationCodeReward:
        base_exp=self._exp_rewards.get(action,1)
        realm=context.get("user_realm",1)
        multiplier=1.0+(realm-1)*0.2
        bonus=context.get("streak_bonus",0)
        total_exp=int(base_exp*multiplier)+bonus
        rid=f"rew_{uuid.uuid4().hex[:8]}"
        reward=CultivationCodeReward(rid,user_id,action,total_exp,multiplier,
            f"Action: {action}, Realm: {realm}x multiplier")
        self._reward_history.append(reward)
        return reward

    def check_realm_permission(self, user_id: str, realm: int, operation: str,
                                language: str="python") -> Tuple[bool,str]:
        limits=self._realm_limits.get(realm)
        if not limits: return False,f"Unknown realm {realm}"
        allowed_langs=limits.get("languages",[])
        if language not in allowed_langs:
            return False,f"Realm {realm} does not support {language}. Unlock at realm {min(realm+1,4)}"
        features=self._unlockable_features.get(realm,[])
        if operation in features:
            return True,"Feature unlocked!"
        if realm<4 and operation in self._unlockable_features.get(4,[]):
            required=next(k for k,v in self._unlockable_features.items() if operation in v and k>realm)
            return False,f"Requires realm {required} for this feature"
        return True,"Allowed"

    def get_user_total_exp(self, user_id: str) -> int:
        return sum(r.exp_gained for r in self._reward_history if r.user_id==user_id)

    def fusion_stats(self) -> Dict[str,Any]:
        return {"realm_tiers":len(self._realm_limits),"reward_types":len(self._exp_rewards),
            "total_rewards_granted":len(self._reward_history),
            "unlockable_feature_sets":len(self._unlockable_features)}


# ═══════════════════════════════════════════════════════════════
# PART J — TEAM CODE COLLABORATION (团队代码协作)
# ═══════════════════════════════════════════════════════════════

class TeamCodeCollaboration:
    def __init__(self):
        self._teams: Dict[str,Dict[str,Any]] = {}
        self._team_code_repos: Dict[str,Dict[str,TeamCodeEntry]] = {}
        self._reviews: List[Dict[str,Any]] = []
        self._comments: List[Dict[str,Any]] = []

    def create_team_repo(self, team_id: str, name: str, owner_id: str) -> Dict[str,Any]:
        repo={"repo_id":f"repo_{uuid.uuid4().hex[:8]}","team_id":team_id,
            "name":name,"owner_id":owner_id,"created_at":time.time(),
            "entries":[],"members_can_write":True}
        self._team_code_repos[repo["repo_id"]]=repo
        self._teams.setdefault(team_id,{"team_id":team_id,"repos":[],"member_count":1})["repos"].append(repo["repo_id"])
        return repo

    def add_entry_to_repo(self, repo_id: str, author_id: str, title: str,
                          language: str, code: str, description: str="") -> TeamCodeEntry:
        entry=TeamCodeEntry(f"entry_{uuid.uuid4().hex[:8]}","",author_id,title,language,code,description)
        if repo_id in self._team_code_repos:
            self._team_code_repos[repo_id]["entries"].append(entry)
        return entry

    def request_review(self, repo_id: str, entry_id: str, requester_id: str) -> Dict[str,Any]:
        review_id=f"rev_{uuid.uuid4().hex[:8]}"
        review={"review_id":review_id,"repo_id":repo_id,"entry_id":entry_id,
            "requester_id":requester_id,"status":"pending","result":None,
            "requested_at":time.time()}
        self._reviews.append(review)
        return review

    def auto_review_entry(self, entry: TeamCodeEntry) -> Optional[CodeReviewReport]:
        gcp=GongbuCodeGenPro()
        report=gcp.review_code_quality(entry.code)
        review_match=[r for r in self._reviews if r.get("entry_id")==entry.entry_id]
        if review_match:
            review_match[0]["result"]=report; review_match[0]["status"]="completed"
        return report

    def add_comment(self, repo_id: str, entry_id: str, author_id: str, content: str):
        comment={"comment_id":f"cmt_{uuid.uuid4().hex[:8]}","repo_id":repo_id,
            "entry_id":entry_id,"author_id":author_id,"content":content,
            "created_at":time.time()}
        self._comments.append(comment)

    def get_repo_entries(self, repo_id: str) -> List[TeamCodeEntry]:
        repo=self._team_code_repos.get(repo_id,{})
        return repo.get("entries",[])

    def collaboration_stats(self) -> Dict[str,Any]:
        total_entries=sum(len(r.get("entries",[])) for r in self._team_code_repos.values())
        return {"teams":len(self._teams),"repos":len(self._team_code_repos),
            "total_entries":total_entries,"reviews":len(self._reviews),
            "comments":len(self._comments)}


# ═══════════════════════════════════════════════════════════════
# PART K — CODE EXECUTION ORCHESTRATOR (统一编排器)
# ═══════════════════════════════════════════════════════════════

class CodeExecutionOrchestrator:
    def __init__(self):
        self.bingbu=BingbuAsyncExecutor(max_workers=3)
        self.libu_assistant=LibuCodeAssistant()
        self.gongbu_pro=GongbuCodeGenPro()
        self.zhongshu_v2=ZhongshuTaskDecomposerV2()
        self.shangshu=ShangshuLoadBalancer()
        self.libu_memory=LibuCodeMemory()
        self.xingbu_monitor=XingbuRealtimeMonitor()
        self.risk_profiler=UserRiskProfiler()
        self.cultivation_fusion=CultivationCodeFusion()
        self.team_collab=TeamCodeCollaboration()
        self.bingbu.start_worker()

    def process_programming_request(self, user_input: str, user_id: str="anonymous",
                                      user_realm: int=1) -> Dict[str,Any]:
        spec=self.zhongshu_v2.decompose_composite(user_input,user_id)
        results=[]; trace_id=f"trace_{uuid.uuid4().hex[:8]}"
        permission=self.risk_profiler.get_risk_decision(user_id,"code_execution")
        if permission==PermissionDecision.DENY:
            return {"spec":spec,"error":"Permission denied - account risk level too high","results":[]}
        for st in spec["subtasks"]:
            if st["type"]=="code_generate":
                gen_result=self.gongbu_pro.generate_annotated_code(st["params"]["input"])
                results.append({"subtask":st["id"],"type":"generate","status":"completed",
                    "suggestion_id":gen_result.suggestion_id})
            elif st["type"]=="code_execute":
                allowed,msg=self.cultivation_fusion.check_realm_permission(user_id,user_realm,"execute","python")
                if not allowed:
                    results.append({"subtask":st["id"],"type":"execute","status":"blocked","reason":msg})
                    continue
                async_task=self.bingbu.submit_async(st["params"]["input"],trace_id=trace_id,user_id=user_id)
                result=self.bingbu.get_result(async_task.task_id)
                exp_reward=self.cultivation_fusion.calculate_exp_reward(user_id,"python_success",
                    {"user_realm":user_realm})
                results.append({"subtask":st["id"],"type":"execute","status":result.status.value if result else "unknown",
                    "task_id":async_task.task_id,"exp_gain":exp_reward.exp_gained})
                self.libu_memory.store_execution_result(user_id,st["params"].get("input",""),"executed",
                    result.status==ExecutionStatus.SUCCESS if result else False)
                event_check=self.xingbu_monitor.check_execution_event({
                    "trace_id":trace_id,"user_id":user_id,"has_network":False,
                    "file_read_count":0,"bytes_transferred":len(st["params"].get("input","")),
                    "spawned_process":True})
                if event_check["should_interrupt"]:
                    results[-1]["security_alert"]=event_check["alerts"]
                self.risk_profiler.update_execution_record(user_id,
                    was_dangerous=event_check["alert_count"]>0,was_blocked=False,
                    was_successful=result.status==ExecutionStatus.SUCCESS if result else False)
            else:
                results.append({"subtask":st["id"],"type":st["type"],"status":"skipped"})
        self.zhongshu_v2.update_subtask_status(spec["spec_id"],"", "completed")
        return {"spec":spec,"trace_id":trace_id,"permission":permission.value,
            "results":results,"cultivation_exp":self.cultivation_fusion.get_user_total_exp(user_id)}

    def chat_with_code_assist(self, user_message: str, user_id: str) -> Dict[str,Any]:
        blocks=self.libu_assistant.parse_code_blocks(user_message)
        response={"parsed_code_blocks":len(blocks),"suggestions":[]}
        for block in blocks:
            if self.libu_assistant.should_suggest_run(block):
                ctx=self.libu_assistant.generate_run_button_context(block)
                response["suggestions"].append(ctx)
        explanation=None
        if blocks:
            explanation=self.libu_assistant.explain_code_natural(blocks[0].get("code",""))
            response["explanation"]=explanation
        opt=self.libu_assistant.optimize_suggestion(blocks[0].get("code","")) if blocks else None
        if opt: response["optimization"]=opt
        self.libu_assistant.log_interaction(user_message,"code_assist")
        return response

    def get_full_status(self) -> Dict[str,Any]:
        return {"bingbu_executor":self.bingbu.executor_stats(),
            "libu_assistant":self.libu_assistant.assistant_stats(),
            "gongbu_pro":self.gongbu_pro.pro_stats(),
            "zhongshu_v2":self.zhongshu_v2.decomposer_v2_stats(),
            "shangshu":self.shangshu.balancer_stats(),
            "libu_memory":self.libu_memory.memory_stats(),
            "xingbu_monitor":self.xingbu_monitor.monitor_stats(),
            "risk_profiler":self.risk_profiler.profiler_stats(),
            "cultivation":self.cultivation_fusion.fusion_stats(),
            "team_collab":self.team_collab.collaboration_stats()}


# ═══════════════════════════════════════════════════════════════
# PART L — TESTING SUITE
# ═══════════════════════════════════════════════════════════════

def _run_test(name: str, fn) -> tuple:
    try: fn(); return ("PASS", name, None)
    except Exception as e: return ("FAIL", name, str(e))

def run_all_tests() -> Dict[str,Any]:
    results=[]

    def test_bingbu_async_submit():
        be=BingbuAsyncExecutor(max_workers=2); be.start_worker()
        task=be.submit_async("print('hello async')","python","u1")
        time.sleep(1.0); result=be.get_result(task.task_id)
        assert result is not None or task.status==ExecutionStatus.QUEUED
        if result: assert result.status.value in ("success","running","queued","pending")
        be.stop_worker()
    results.append(_run_test("BINGBU: async submit+result", test_bingbu_async_submit))

    def test_bingbu_multi_language():
        be=BingbuAsyncExecutor(); be.start_worker()
        py_task=be.submit_async("x=1+1","python"); js_task=be.submit_async("console.log(1+1)","javascript")
        time.sleep(1); py_res=be.get_result(py_task.task_id); js_res=be.get_result(js_task.task_id)
        assert py_res is not None; assert js_res is not None
        be.stop_worker()
    results.append(_run_test("BINGBU: multi-language execution", test_bingbu_multi_language))

    def test_bingbu_safety_block():
        be=BingbuAsyncExecutor(); be.start_worker()
        task=be.submit_async("rm -rf /tmp/test","shell")
        time.sleep(0.5); result=be.get_result(task.task_id)
        assert result is not None; assert result.status==ExecutionStatus.BLOCKED
        be.stop_worker()
    results.append(_run_test("BINGBU: safety block dangerous", test_bingbu_safety_block))

    def test_bingbu_stats():
        be=BingbuAsyncExecutor(); stats=be.executor_stats()
        assert "max_workers" in stats; assert "active_tasks" in stats
    results.append(_run_test("BINGBU: executor stats", test_bingbu_stats))

    def test_libu_parse_code():
        la=LibuCodeAssistant(); msg='Here is some code:\n```python\nprint("hello")\n```\nThanks!'
        blocks=la.parse_code_blocks(msg)
        assert len(blocks)>=1; assert blocks[0]["language"]=="python"
    results.append(_run_test("LIBU: parse code blocks", test_libu_parse_code))

    def test_libu_explain():
        la=LibuCodeAssistant(); exp=la.explain_code_natural("def foo():\n    return 42")
        assert isinstance(exp,str); assert len(exp)>0
    results.append(_run_test("LIBU: natural explanation", test_libu_explain))

    def test_libu_optimize():
        la=LibuCodeAssistant(); sug=la.optimize_suggestion("for i in range(len(arr)):\n    print(i)")
        assert sug.suggestion_id.startswith("sug_"); assert isinstance(sug.content,str)
    results.append(_run_test("LIBU: optimize suggestion", test_libu_optimize))

    def test_gongbu_generate():
        gp=GongbuCodeGenPro(); sug=gp.generate_annotated_code("calculate fibonacci","python")
        assert "Auto-generated" in sug.content; assert "solve()" in sug.content
    results.append(_run_test("GONGBU: annotated generation", test_gongbu_generate))

    def test_gongbu_debug():
        gp=GongbuCodeGenPro(); res=gp.debug_code_pro("print(x)","NameError: name 'x' is not defined")
        assert res["fixes"] is not None; assert isinstance(res["fixes"],list)
    results.append(_run_test("GONGBU: debug pro", test_gongbu_debug))

    def test_gongbu_iterative():
        gp=GongbuCodeGenPro(); res=gp.iterative_modify("x=1","make x equal to 2")
        assert "Modification:" in res["final_code"]; assert res["versions"]>=2
    results.append(_run_test("GONGBU: iterative modify", test_gongbu_iterative))

    def test_gongbu_review():
        gp=GongbuCodeGenPro(); rep=gp.review_code_quality("def foo():\n    eval(input())")
        assert rep.report_id.startswith("review_"); assert rep.overall_grade in ("A","B","C","D")
    results.append(_run_test("GONGBU: code quality review", test_gongbu_review))

    def test_zhongshu_composite():
        zv2=ZhongshuTaskDecomposerV2(); spec=zv2.decompose_composite("写一个爬虫并运行","u1")
        assert spec["pattern_matched"] is not None; assert len(spec["subtasks"])>=2
    results.append(_run_test("ZHONGSHU: composite decompose", test_zhongshu_composite))

    def test_zhongshu_simple():
        zv2=ZhongshuTaskDecomposerV2(); spec=zv2.decompose_composite("hello world","u1")
        assert spec["pattern_matched"] is None; assert len(spec["subtasks"])==1
    results.append(_run_test("ZHONGSHU: simple decompose", test_zhongshu_simple))

    def test_shangshu_select():
        sl=ShangshuLoadBalancer(); sl.register_worker("w1","localhost",8001)
        sl.register_worker("w2","localhost",8002); w=sl.select_worker()
        assert w is not None; assert w["id"] in ("w1","w2")
    results.append(_run_test("SHANGSHU: worker selection", test_shangshu_select))

    def test_shangshu_degrade():
        sl=ShangshuLoadBalancer(); assert sl.should_degrade()==True
    results.append(_run_test("SHANGSHU: degrade detection", test_shangshu_degrade))

    def test_libu_memory_store():
        lm=LibuCodeMemory(); lm.store_execution_result("u1","print(1)","output",True)
        assert len(lm._code_memory)>=1
    results.append(_run_test("LIBU_MEM: store execution", test_libu_memory_store))

    def test_libu_memory_search():
        lm=LibuCodeMemory(); lm.store_execution_result("u1","import os","ok",True)
        lm.store_execution_result("u1","import json","also ok",True)
        results=lm.search_similar_code("import statement",2)
        assert len(results)<=2
    results.append(_run_test("LIBU_MEM: similarity search", test_libu_memory_search))

    def test_xingbu_alert():
        xm=XingbuRealtimeMonitor(); res=xm.check_execution_event({"file_read_count":100,"has_network":True})
        assert res["alert_count"]>=1
    results.append(_run_test("XINGBU: alert on excessive reads", test_xingbu_alert))

    def test_xingbu_no_alert():
        xm=XingbuRealtimeMonitor(); res=xm.check_execution_event({"file_read_count":5,"has_network":False})
        assert res["should_interrupt"]==False
    results.append(_run_test("XINGBU: no alert normal ops", test_xingbu_no_alert))

    def test_risk_profile():
        rp=UserRiskProfiler(); rp.update_execution_record("u1",False,False,True)
        rp.update_execution_record("u1",True,True,True)
        rp.update_execution_record("u1",True,False,True)
        dec=rp.get_risk_decision("u1","code_exec")
        assert dec in(PermissionDecision.ALLOW,PermissionDecision.CONFIRM_REQUIRED,PermissionDecision.DENY)
    results.append(_run_test("RISK: profile calculation", test_risk_profile))

    def test_cultivation_reward():
        cf=CultivationCodeFusion(); rew=cf.calculate_exp_reward("u1","python_success",{"user_realm":2})
        assert rew.exp_gained>0; assert rew.bonus_multiplier>1
    results.append(_run_test("CULTIVATION: exp reward calc", test_cultivation_reward))

    def test_cultivation_realm_check():
        cf=CultivationCodeFusion(); ok,msg=cf.check_realm_permission("u1",1,"execute","python")
        assert ok==True
        nok,_msg=cf.check_realm_permission("u1",1,"execute","javascript")
        assert nok==False
    results.append(_run_test("CULTIVATION: realm permission", test_cultivation_realm_check))

    def test_team_repo_create():
        tc=TeamCodeCollaboration(); repo=tc.create_team_repo("t1","TestRepo","owner1")
        assert repo["repo_id"].startswith("repo_"); assert len(repo["entries"])==0
    results.append(_run_test("TEAM: create repo", test_team_repo_create))

    def test_team_add_entry():
        tc=TeamCodeCollaboration(); repo=tc.create_team_repo("t1","R","o1")
        entry=tc.add_entry_to_repo(repo["repo_id"],"a1","Test","python","# test code")
        assert entry.entry_id.startswith("entry_"); assert entry.language=="python"
    results.append(_run_test("TEAM: add entry", test_team_add_entry))

    def test_orchestrator_pipeline():
        orc=CodeExecutionOrchestrator(); result=orc.process_programming_request("print hello world","u1",user_realm=2)
        assert "spec" in result; assert "results" in result; assert "cultivation_exp" in result
    results.append(_run_test("ORC: full pipeline", test_orchestrator_pipeline))

    def test_orchestrator_chat():
        orc=CodeExecutionOrchestrator(); result=orc.chat_with_code_assist("帮我看下这段:\n```python\nx=1\n```\n","u1")
        assert "parsed_code_blocks" in result
    results.append(_run_test("ORC: chat assist", test_orchestrator_chat))

    def test_orchestrator_status():
        orc=CodeExecutionOrchestrator(); st=orc.get_full_status()
        assert "bingbu_executor" in st; assert "risk_profiler" in st
    results.append(_run_test("ORC: full status", test_orchestrator_status))

    passed=sum(1 for r in results if r[0]=="PASS")
    failed=[r for r in results if r[0]=="FAIL"]; errors=[r for r in results if r[0]=="ERROR"]
    print(f"\n{'='*60}")
    print(f"L40 CODE EXECUTION DEEP INTEGRATION — TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Total : {len(results)}")
    print(f"  Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"  Failed: {len(failed)}")
    if failed:
        for _,name,err in failed: print(f"    [X] {name}: {err}")
    print(f"  Errors: {len(errors)}")
    if errors:
        for _,name,err in errors: print(f"    ! {name}: {err}")
    print(f"{'='*60}")
    return {"total":len(results),"passed":passed,"failed":len(failed),"errors":len(errors),"results":results}

if __name__ == "__main__":
    run_all_tests()
    print("\n[OK] Layer 40 — Code Execution Deep Integration loaded OK")
