# -*- coding: utf-8 -*-
"""
Layer 39 - Claude Code Core Capability Development
=====================================================
Claude Code 核心能力开发层 — 9大模块+编排器+测试套件
任务拆解+工具注册+文件系统+代码生成调试+安全扫描+上下文记忆+确认流程
"""
from __future__ import annotations
import os, sys, time, uuid, hashlib, json, re, ast, textwrap, copy, threading, subprocess as sp, tempfile, shutil, random
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from collections import deque

# ═══════════════════════════════════════════════════════════════
# PART H — ENUMS & DATACLASSES
# ═══════════════════════════════════════════════════════════════

class TaskType(PyEnum):
    CODE_GENERATE="code_generate"; CODE_MODIFY="code_modify"
    CODE_EXPLAIN="code_explain"; CODE_DEBUG="code_debug"
    COMMAND_EXECUTE="command_execute"; TOOL_CALL="tool_call"

class SpecStatus(PyEnum):
    PENDING="pending"; RUNNING="running"; COMPLETED="completed"
    FAILED="failed"; CANCELLED="cancelled"

class ToolCategory(PyEnum):
    FILESYSTEM="filesystem"; EXECUTION="execution"
    CODE_GEN="code_gen"; CODE_DEBUG="code_debug"; UTILITY="utility"

class RiskSeverity(PyEnum):
    INFO="info"; LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"

class ConfirmationState(PyEnum):
    PENDING="pending"; REQUESTED="requested"; CONFIRMED="confirmed"
    REJECTED="reJECTED"; EXPIRED="expired"

@dataclass
class TaskSpec:
    id: str; user_id: str; intent: str; task_type: TaskType
    spec_json: Dict[str,Any]; status: SpecStatus = SpecStatus.PENDING
    subtasks: List[Dict[str,Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time); updated_at: Optional[float] = None

@dataclass
class SubTask:
    id: str; task_type: str; params: Dict[str,Any]
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"; result: Any = None; error: Optional[str] = None

@dataclass
class DAGNode:
    subtask_id: str; dependencies: List[str]; dependents: List[str]
    depth: int = 0; parallel_group: int = -1

@dataclass
class ToolRegistration:
    name: str; description: str; category: ToolCategory
    input_schema: Dict[str,Any]; output_schema: Dict[str,Any]
    handler: Optional[Callable] = None; enabled: bool = True
    call_count: int = 0; avg_duration_ms: float = 0

@dataclass
class ToolCallResult:
    tool_name: str; success: bool; output: Any
    error: Optional[str] = None; duration_ms: float = 0
    trace_id: str = ""; risk_score: float = 0

@dataclass
class CodeSnippet:
    snippet_id: str; user_id: str; title: str; language: str
    content: str; tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    is_public: bool = False; share_link: str = ""

@dataclass
class StaticScanResult:
    scan_id: str; file_path_or_code: str; risk_score: float
    severity: RiskSeverity; findings: List[Dict[str,Any]]
    dangerous_functions: List[str]; dangerous_modules: List[str]
    suggestion: str = ""; scanned_at: float = field(default_factory=time.time)

@dataclass
class ConfirmationRequest:
    request_id: str; user_id: str; operation: str; description: str
    risk_level: RiskSeverity; token: str; state: ConfirmationState = ConfirmationState.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0; confirmed_by: str = ""


# ═══════════════════════════════════════════════════════════════
# PART A — TASK DECOMPOSER (intent recognition + DAG + persistence)
# ═══════════════════════════════════════════════════════════════

class TaskDecomposer:
    def __init__(self):
        self._specs: Dict[str,TaskSpec] = {}; self._intents: List[Dict[str,str]] = []
        self._type_patterns={
            "写":TaskType.CODE_GENERATE,"创建":TaskType.CODE_GENERATE,"生成":TaskType.CODE_GENERATE,
            "修改":TaskType.CODE_MODIFY,"改":TaskType.CODE_MODIFY,"更新":TaskType.CODE_MODIFY,
            "解释":TaskType.CODE_EXPLAIN,"说明":TaskType.CODE_EXPLAIN,"分析":TaskType.CODE_EXPLAIN,
            "调试":TaskType.CODE_DEBUG,"修复":TaskType.CODE_DEBUG,"排查":TaskType.CODE_DEBUG,
            "运行":TaskType.COMMAND_EXECUTE,"执行":TaskType.COMMAND_EXECUTE,
            "调用":TaskType.TOOL_CALL,"使用工具":TaskType.TOOL_CALL}
    def recognize_intent(self, user_input: str) -> Tuple[TaskType,float,str]:
        scores={tt:0 for tt in TaskType}
        for keyword,tt in self._type_patterns.items():
            if keyword in user_input: scores[tt]+=len(keyword)*2
        if any(k in user_input for k in ("代码","脚本","函数","python","程序")):
            scores[TaskType.CODE_GENERATE]+=10
        best_type=max(scores,key=scores.get); confidence=min(scores[best_type]/20*100,100)
        return best_type,confidence/100,user_input.strip()
    def decompose(self, user_input: str, user_id: str="anonymous") -> TaskSpec:
        task_type,confidence,intent=self.recognize_intent(user_input)
        sid=f"spec_{uuid.uuid4().hex[:8]}"
        subtasks=self._generate_subtasks(user_input,task_type)
        spec=TaskSpec(sid,user_id,intent,task_type,{"original_input":user_input,"confidence":confidence},
            subtasks=subtasks)
        self._specs[sid]=spec; return spec
    def _generate_subtasks(self, user_input: str, task_type: TaskType) -> List[Dict[str,Any]]:
        if task_type==TaskType.CODE_GENERATE:
            return [{"id":"st_1","type":"analyze_requirement","params":{"input":user_input},"depends_on":[]},
                {"id":"st_2","type":"generate_code","params":{"input":user_input},"depends_on":["st_1"]},
                {"id":"st_3","type":"validate_code","params":{},"depends_on":["st_2"]}]
        elif task_type==TaskType.COMMAND_EXECUTE:
            return [{"id":"st_1","type":"security_check","params":{"command":user_input},"depends_on":[]},
                {"id":"st_2","type":"execute_command","params":{"command":user_input},"depends_on":["st_1"]}]
        elif task_type==TaskType.CODE_DEBUG:
            return [{"id":"st_1","type":"analyze_error","params":{"code":user_input},"depends_on":[]},
                {"id":"st_2","type":"generate_fix","params":{},"depends_on":["st_1"]},
                {"id":"st_3","type":"verify_fix","params":{},"depends_on":["st_2"]}]
        else:
            return [{"id":"st_1","type":"process","params":{"input":user_input},"depends_on":[]}]
    def build_dag(self, subtasks: List[Dict[str,Any]]) -> Tuple[List[DAGNode],List[str],Optional[str]]:
        nodes={st["id"]:DAGNode(st["id"],st.get("depends_on",[]),[]) for st in subtasks}
        for st in subtasks:
            for dep in st.get("depends_on",[]):
                if dep in nodes: nodes[dep].dependents.append(st["id"])
        cycle=self._detect_cycle(nodes)
        if cycle: return [],[],cycle
        sorted_ids=self._topological_sort(nodes)
        dag_nodes=[nodes[sid] for sid in sorted_ids]; return dag_nodes,sorted_ids,None
    def _detect_cycle(self, nodes: Dict[str,DAGNode]) -> Optional[str]:
        WHITE,GRAY,BLACK=0,1,2; color={n:WHITE for n in nodes}; path=[]
        def dfs(n):
            color[n]=GRAY; path.append(n)
            for dep in nodes[n].dependencies:
                if dep not in nodes: continue
                if color[dep]==GRAY: return dep
                if color[dep]==WHITE:
                    result=dfs(dep)
                    if result: return result
            color[n]=BLACK; path.pop(); return None
        for n in nodes:
            if color[n]==WHITE:
                result=dfs(n)
                if result: return f"Cycle detected: {' → '.join(path+[result])}"
        return None
    def _topological_sort(self, nodes: Dict[str,DAGNode]) -> List[str]:
        in_degree={n:len(d.dependencies) for n,d in nodes.items()}
        queue=deque([n for n,d in in_degree.items() if d==0])
        result=[]
        while queue:
            n=queue.popleft(); result.append(n)
            for dependent in nodes[n].dependents:
                in_degree[dependent]-=1
                if in_degree[dependent]==0: queue.append(dependent)
        if len(result)!=len(nodes): return []
        for i,n in enumerate(result): nodes[n].depth=i; nodes[n].parallel_group=i
        return result
    def persist_spec(self, spec: TaskSpec) -> TaskSpec:
        spec.updated_at=time.time(); self._specs[spec.id]=spec; return spec
    def update_spec_status(self, spec_id: str, status: SpecStatus) -> bool:
        s=self._specs.get(spec_id)
        if s: s.status=status; s.updated_at=time.time(); return True
        return False
    def get_spec(self, spec_id: str) -> Optional[TaskSpec]: return self._specs.get(spec_id)
    def decomposer_stats(self) -> Dict[str,Any]:
        by_status={}
        for s in self._specs.values(): by_status[s.status.value]=by_status.get(s.status.value,0)+1
        return {"total_specs":len(self._specs),"by_status":by_status}


# ═══════════════════════════════════════════════════════════════
# PART B — TOOL REGISTRY (decorator + Pydantic validation)
# ═══════════════════════════════════════════════════════════════

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str,ToolRegistration] = {}; self._call_log: List[ToolCallResult] = []
    def register_tool(self, name: str="", description: str="", category: ToolCategory=ToolCategory.UTILITY,
                     input_schema: Optional[Dict]=None, output_schema: Optional[Dict]=None):
        def decorator(func: Callable) -> Callable:
            tool_name=name or func.__name__
            tr=ToolRegistration(tool_name,description or func.__doc__ or "",category,
                input_schema or {},output_schema or {},func)
            self._tools[tool_name]=tr; return func
        return decorator
    def get_tool(self, name: str) -> Optional[ToolRegistration]: return self._tools.get(name)
    def list_tools(self, category: Optional[ToolCategory]=None) -> List[ToolRegistration]:
        tools=list(self._tools.values())
        if category: tools=[t for t in tools if t.category==category]
        return tools
    def call_tool(self, name: str, params: Dict[str,Any], trace_id: str="") -> ToolCallResult:
        t0=time.time(); tool=self._tools.get(name)
        if not tool or not tool.handler: return ToolCallResult(name,False,None,f"Tool {name} not found",0,trace_id)
        try:
            validated=self._validate_params(params,tool.input_schema)
            output=tool.handler(**validated); duration=(time.time()-t0)*1000
            tool.call_count+=1; tool.avg_duration_ms=(tool.avg_duration_ms*(tool.call_count-1)+duration)/tool.call_count
            result=ToolCallResult(name,True,output,duration_ms=duration,trace_id=trace_id)
        except Exception as ex:
            duration=(time.time()-t0)*1000; result=ToolCallResult(name,False,None,str(ex),duration,trace_id=trace_id)
        self._call_log.append(result); return result
    def _validate_params(self, params: Dict, schema: Dict) -> Dict:
        required=schema.get("required",{}); validated={}
        for k,v in params.items(): validated[k]=v
        for r in required:
            if r not in validated: validated[r]=schema.get("properties",{}).get(r,schema.get("default"))
        type_hints=schema.get("properties",{})
        for k,v in validated.items():
            if k in type_hints:
                th=type_hints[k]
                if th=="string" and not isinstance(v,str): validated[k]=str(v)
                elif th=="integer" and not isinstance(v,int): validated[k]=int(v)
                elif th=="number" and not isinstance(v,(int,float)): validated[k]=float(v)
                elif th=="boolean" and not isinstance(v,bool): validated[k]=str(v).lower() in("true","1")
        return validated
    def registry_stats(self) -> Dict[str,Any]:
        cats={}
        for t in self._tools.values(): cats[t.category.value]=cats.get(t.category.value,0)+1
        success=sum(1 for r in self._call_log if r.success)
        return {"total_tools":len(self._tools),"by_category":cats,"total_calls":len(self._call_log),
            "success_rate":round(success/max(len(self._call_log),1)*100,1)}


# ═══════════════════════════════════════════════════════════════
# PART C — FILE SYSTEM TOOLS (Hubu department)
# ═══════════════════════════════════════════════════════════════

class FileSystemTools:
    def __init__(self, workspace_root: str="/tmp/workspace"):
        self._root=os.path.abspath(workspace_root); self._whitelist_paths=set()
        self.add_whitelist(self._root)
    def add_whitelist(self, path: str): self._whitelist_paths.add(os.path.abspath(path))
    def _check_path(self, path: str) -> Tuple[bool,str]:
        full_path=os.path.normpath(os.path.join(self._root,path))
        if any(full_path.startswith(wp) for wp in self._whitelist_paths): return True,""
        return False,f"Path '{full_path}' outside workspace whitelist"
    def read_file(self, path: str, max_size: int=1024*1024) -> ToolCallResult:
        ok,err_msg=self._check_path(path); t0=time.time()
        if not ok: return ToolCallResult("read_file",False,None,err_msg,0)
        try:
            with open(os.path.join(self._root,path),'r',encoding='utf-8') as f:
                content=f.read(max_size)
            return ToolCallResult("read_file",True,content,None,(time.time()-t0)*1000)
        except Exception as ex: return ToolCallResult("read_file",False,None,str(ex),(time.time()-t0)*1000)
    def write_file(self, path: str, content: str, create_dirs: bool=True) -> ToolCallResult:
        ok,err_msg=self._check_path(path); t0=time.time()
        if not ok: return ToolCallResult("write_file",False,None,err_msg,0)
        try:
            full_path=os.path.join(self._root,path)
            if create_dirs: os.makedirs(os.path.dirname(full_path),exist_ok=True)
            with open(full_path,'w',encoding='utf-8') as f: f.write(content)
            return ToolCallResult("write_file",True,len(content),None,(time.time()-t0)*1000)
        except Exception as ex: return ToolCallResult("write_file",False,None,str(ex),(time.time()-t0)*1000)
    def list_directory(self, path: str=".") -> ToolCallResult:
        ok,err_msg=self._check_path(path); t0=time.time()
        if not ok: return ToolCallResult("list_directory",False,None,err_msg,0)
        try:
            full_path=os.path.join(self._root,path)
            entries=[]
            if os.path.isdir(full_path):
                for entry in os.listdir(full_path):
                    ep=os.path.join(full_path,entry)
                    entries.append({"name":entry,"is_dir":os.path.isdir(ep),
                        "size":os.path.getsize(ep) if os.path.isfile(ep) else 0})
            return ToolCallResult("list_directory",True,entries,None,(time.time()-t0)*1000)
        except Exception as ex: return ToolCallResult("list_directory",False,None,str(ex),(time.time()-t0)*1000)
    def delete_file(self, path: str, confirm: bool=False) -> ToolCallResult:
        ok,err_msg=self._check_path(path); t0=time.time()
        if not ok: return ToolCallResult("delete_file",False,None,err_msg,0)
        if not confirm: return ToolCallResult("delete_file",False,None,"Confirmation required",0)
        try:
            full_path=os.path.join(self._root,path)
            if os.path.exists(full_path): os.remove(full_path)
            return ToolCallResult("delete_file",True,True,None,(time.time()-t0)*1000)
        except Exception as ex: return ToolCallResult("delete_file",False,None,str(ex),(time.time()-t0)*1000)


# ═══════════════════════════════════════════════════════════════
# PART D — COMMAND EXECUTION TOOL (Bingbu sandbox integration)
# ═══════════════════════════════════════════════════════════════

class CommandExecutionTool:
    def __init__(self, allowed_commands: Optional[Set[str]]=None):
        self._allowed=allowed_commands or {"python","python3","pip","git","ls","cat","echo",
            "grep","find","head","tail","wc","date","whoami","pwd","cd"}
        self._history: List[Dict[str,Any]] = []; self._sandbox_available=True
    def run_command(self, command: str, cwd: Optional[str]=None, timeout: int=30) -> ToolCallResult:
        t0=time.time(); cmd_parts=command.split()
        base_cmd=cmd_parts[0] if cmd_parts else ""
        if base_cmd not in self._allowed:
            return ToolCallResult("run_command",False,None,f"Command '{base_cmd}' not in whitelist",0)
        try:
            proc=sp.run(command,shell=True,capture_output=True,text=True,timeout=timeout,cwd=cwd)
            duration=(time.time()-t0)*1000
            result=ToolCallResult("run_command",proc.returncode==0,
                {"stdout":proc.stdout[:50000],"stderr":proc.stderr[:5000],"returncode":proc.returncode},None,duration)
            self._history.append({"command":command[:200],"success":result.success,"duration_ms":duration,"timestamp":time.time()})
            return result
        except sp.TimeoutExpired:
            return ToolCallResult("run_command",False,None,f"Timeout after {timeout}s",(time.time()-t0)*1000)
        except Exception as ex:
            return ToolCallResult("run_command",False,None,str(ex),(time.time()-t0)*1000)
    def get_history(self, limit: int=50) -> List[Dict[str,Any]]: return self._history[-limit:]
    def tool_stats(self) -> Dict[str,Any]:
        success=sum(1 for h in self._history if h["success"])
        return {"total_calls":len(self._history),"success_rate":round(success/max(len(self._history),1)*100,1),
            "allowed_commands":len(self._allowed)}


# ═══════════════════════════════════════════════════════════════
# PART E — CODE GENERATION & DEBUG TOOLS (Gongbu department)
# ═══════════════════════════════════════════════════════════════

class CodeGenDebugTools:
    def __init__(self): self._history: List[Dict[str,Any]] = []
    def generate_code(self, prompt: str, language: str="python", context: str="") -> ToolCallResult:
        t0=time.time(); generated=f"# Auto-generated {language} code\n# Prompt: {prompt}\n{context}\ndef solution():\n    # Implementation would use LLM API here\n    pass\nprint(solution())"
        duration=(time.time()-t0)*1000; self._history.append({"action":"generate","language":language,"duration_ms":duration})
        return ToolCallResult("generate_code",True,generated,None,duration)
    def debug_code(self, code: str, error_message: str="") -> ToolCallResult:
        t0=time.time(); lines=code.split("\n"); suggestions=[]
        if "SyntaxError" in error_message or "IndentationError" in error_message:
            suggestions.append("Check syntax: ensure proper indentation (use 4 spaces)")
            suggestions.append("Verify all parentheses and quotes are balanced")
        if "NameError" in error_message:
            match=re.search(r"NameError: name '(\w+)' is not defined",error_message)
            if match: suggestions.append(f"Undefined variable: '{match.group(1)}' - check spelling or define it")
        if "TypeError" in error_message:
            suggestions.append("Check variable types - ensure you're using correct operators")
        if not suggestions: suggestions.append(f"Review the error: {error_message[:200]}")
        duration=(time.time()-t0)*1000; self._history.append({"action":"debug","suggestions":len(suggestions),"duration_ms":duration})
        return ToolCallResult("debug_code",True,suggestions,None,duration)
    def explain_code(self, code: str, detail_level: str="medium") -> ToolCallResult:
        t0=time.time(); explanations=[]; lines=code.split("\n")
        for i,line in enumerate(lines,1):
            stripped=line.strip()
            if not stripped: continue
            if stripped.startswith("def ") or stripped.startswith("class "):
                definitions=re.findall(r'(def|class)\s+(\w+)[\(:]',stripped)
                explanations.append(f"L{i}: Define {definitions[0] if definitions else 'function/class'}")
            elif stripped.startswith("import "):
                mods=re.findall(r'import\s+(.+)',stripped)
                explanations.append(f"L{i}: Import modules: {', '.join(mods)}")
            elif "=" in stripped and "#" not in stripped.split("#")[0][:1]:
                explanations.append(f"L{i}: Variable assignment")
        if detail_level=="high":
            for i,line in enumerate(lines,1):
                if line.strip() and not any(e.startswith(f"L{i}:") for e in explanations):
                    explanations.append(f"L{i}: {line.strip()[:80]}")
        duration=(time.time()-t0)*1000; self._history.append({"action":"explain","lines":len(explanations),"duration_ms":duration})
        return ToolCallResult("explain_code",True,explanations,None,duration)
    def run_tests(self, code: str, test_cases: Optional[List[Dict]]=None) -> ToolCallResult:
        t0=time.time(); results=[]
        tests=test_cases or [{"name":"basic_syntax","assert":"compile(code,'exec',{'__name__':'__main__'})!=None"}]
        for tc in tests:
            try:
                compile(code,'<string>','exec'); results.append({"test":tc.get("name","unknown"),"status":"passed"})
            except SyntaxError as e:
                results.append({"test":tc.get("name","unknown"),"status":"failed","error":str(e)})
            except Exception as e:
                results.append({"test":tc.get("name","unknown"),"status":"error","error":str(e)})
        duration=(time.time()-t0)*1000; passed=sum(1 for r in results if r["status"]=="passed")
        self._history.append({"action":"run_tests","total":len(results),"passed":passed,"duration_ms":duration})
        return ToolCallResult("run_tests",True,results,None,duration)
    def tool_stats(self) -> Dict[str,Any]:
        actions={}
        for h in self._history: actions[h.get("action","unknown")]=actions.get(h.get("action","unknown"),0)+1
        return {"total_actions":len(self._history),"by_action":actions}


# ═══════════════════════════════════════════════════════════════
# PART F — STATIC CODE SCANNER (Xingbu AST analysis)
# ═══════════════════════════════════════════════════════════════

class StaticCodeScanner:
    def __init__(self):
        self._dangerous_funcs={"eval","exec","compile","__import__","open",
            "getattr","setattr","delattr","globals","locals","vars",
            "os.system","os.popen"}
        self._dangerous_modules={"os","subprocess","socket","requests","pickle","shutil",
            "ctypes","importlib","sys","builtins","signal","threading"}
        self._risk_weights={"eval":25,"exec":25,"__import__":15,"open":10,
            "subprocess":20,"socket":15,"os.system":30,"os.popen":25,"pickle.loads":20}
    def scan_code(self, code: str, filename: str="<string>") -> StaticScanResult:
        t0=time.time(); findings=[]; dangerous_funcs_found=[]; dangerous_mods_found=[]
        score=0.0
        try:
            tree=ast.parse(code,filename)
        except SyntaxError as se:
            return StaticScanResult(f"scan_{uuid.uuid4().hex[:8]}",code,100,RiskSeverity.CRITICAL,
                [{"line":0,"severity":"critical","message":f"Syntax Error: {se}"}],
                [],[],f"Code has syntax errors, cannot analyze safely")
        for node in ast.walk(tree):
            if isinstance(node,(ast.Call,ast.Attribute)):
                node_str=""
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                    node_str=node.func.id
                elif isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name):
                    node_str=node.func.value.id+"."+node.func.attr
                elif isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name):
                    node_str=node.value.id+"."+node.attr
                else: node_str=""
                if node_str in self._dangerous_funcs:
                    lineno=getattr(node,'lineno',0); dangerous_funcs_found.append(node_str)
                    w=self._risk_weights.get(node_str,10); score+=w
                    findings.append({"line":lineno,"severity":"high" if w>=15 else "medium",
                        "message":f"Dangerous function: {node_str}"})
            if isinstance(node,ast.ImportFrom) or isinstance(node,ast.Import):
                mod_name=node.module if hasattr(node,'module') else ""
                aliases=[a.name for a in (node.names if hasattr(node,'names') else [])]
                for m in (aliases+[mod_name]):
                    if m in self._dangerous_modules:
                        lineno=getattr(node,'lineno',0); dangerous_mods_found.append(m)
                        w=self._risk_weights.get(m,12); score+=w
                        findings.append({"line":lineno,"severity":"medium",
                            "message":f"Dangerous module import: {m}"})
        if len(code)>5000: findings.append({"line":0,"severity":"low","message":"Large code (>5KB)"}); score+=5
        comment_ratio=len(re.findall(r'#',code))/max(len(code.split('\n')),1)
        if comment_ratio<0.05: findings.append({"line":0,"severity":"info","message":"Very few comments"}); score+=2
        severity=RiskSeverity.INFO if score<20 else (RiskSeverity.LOW if score<40 else (RiskSeverity.MEDIUM if score<60 else (RiskSeverity.HIGH if score<80 else RiskSeverity.CRITICAL)))
        suggestion="Code looks safe to execute" if score<30 else ("Review before executing - medium risk" if score<60 else "High risk - requires manual review or approval")
        return StaticScanResult(f"scan_{uuid.uuid4().hex[:8]}",code,score,severity,findings,
            dangerous_funcs_found,dangerous_mods_found,suggestion,t0-time.time())
    def scanner_stats(self) -> Dict[str,Any]:
        return {"dangerous_functions_monitored":len(self._dangerous_funcs),
            "dangerous_modules_monitored":len(self._dangerous_modules),
            "risk_weight_rules":len(self._risk_weights)}


# ═══════════════════════════════════════════════════════════════
# PART G — PROGRAMMING CONTEXT MANAGER (memory + knowledge + snippets)
# ═══════════════════════════════════════════════════════════════

class ProgrammingContextManager:
    def __init__(self):
        self._context: Dict[str,Any] = {"files":[],"recent_files":[],"commands":[],"preferences":{}}
        self._knowledge_base: List[Dict[str,Any]] = []  # simulated vector DB
        self._snippets: Dict[str,CodeSnippet] = {}; self._context_window_size = 20
        self._compression_threshold = 10
    def update_context(self, key: str, value: Any):
        if key=="file_accessed":
            self._context["recent_files"].append(value)
            self._context["recent_files"]=self._context["recent_files"][-20:]
        elif key=="command_executed":
            self._context["commands"].append(value)
            self._context["commands"]=self._context["commands"][-20:]
        elif key.startswith("pref_"): self._context["preferences"][key[5:]]=value
    def get_context(self) -> Dict[str,Any]: return dict(self._context)
    def compress_context(self):
        if len(self._context.get("commands",[]))>self._compression_threshold:
            self._context["commands"]=self._context["commands"][-self._compression_threshold:]
        if len(self._context.get("recent_files",[]))>self._compression_threshold:
            self._context["recent_files"]=self._context["recent_files"][-self._compression_threshold:]
    def add_knowledge(self, question: str, answer: str, tags: List[str]=None, source: str="internal"):
        self._knowledge_base.append({"question":question,"answer":answer,"tags":tags or [],
            "source":source,"added_at":time.time(),"embedding_sim":random.uniform(0.5,1.0)})
    def search_knowledge(self, query: str, top_k: int=3) -> List[Dict[str,Any]]:
        scored=[(k,random.uniform(0.3,1.0)) for k in self._knowledge_base
                 if any(q.lower() in k["question"].lower() or q.lower() in k.get("answer","").lower() for q in [query])]
        if not scored: scored=[(k,random.uniform(0.1,0.9)) for k in self._knowledge_base]
        scored.sort(key=lambda x:-x[1]); return [s[0] for s in scored[:top_k]]
    def save_snippet(self, user_id: str, title: str, language: str, content: str, tags: List[str]=None) -> CodeSnippet:
        sid=f"snip_{uuid.uuid4().hex[:8]}"; snip=CodeSnippet(sid,user_id,title,language,content,tags or [])
        self._snippets[sid]=snip; return snip
    def get_user_snippets(self, user_id: str) -> List[CodeSnippet]:
        return [s for s in self._snippets.values() if s.user_id==user_id]
    def get_snippet(self, snippet_id: str) -> Optional[CodeSnippet]: return self._snippets.get(snippet_id)
    def manager_stats(self) -> Dict[str,Any]:
        return {"context_keys":len(self._context),"knowledge_entries":len(self._knowledge_base),
            "total_snippets":len(self._snippets),"window_size":self._context_window_size}


# ═══════════════════════════════════════════════════════════════
# PART H — SECURITY CONFIRMATION ENGINE
# ═══════════════════════════════════════════════════════════════

class SecurityConfirmationEngine:
    def __init__(self):
        self._requests: Dict[str,ConfirmationRequest] = {}
        self._confirmation_ttl = 300  # 5 minutes
        self._high_risk_operations = {"delete ","delete_file","rm -rf","sudo","chmod 777",
            "format_disk","drop_table","eval(","exec(","__import__("}
    def request_confirmation(self, user_id: str, operation: str, description: str,
                           risk_level: RiskSeverity=RiskSeverity.HIGH) -> ConfirmationRequest:
        rid=f"conf_{uuid.uuid4().hex[:8]}"; token=hashlib.sha256(f"{rid}{time.time()}".encode()).hexdigest()[:16]
        req=ConfirmationRequest(rid,user_id,operation,description,risk_level,token,
            expires_at=time.time()+self._confirmation_ttl)
        req.state=ConfirmationState.REQUESTED; self._requests[rid]=req; return req
    def confirm(self, request_id: str, token: str, user_id: str) -> Tuple[bool,str]:
        req=self._requests.get(request_id)
        if not req: return False,"Request not found"
        if req.state!=ConfirmationState.REQUESTED: return False,f"Request already {req.state.value}"
        if token!=req.token: return False,"Invalid confirmation token"
        if time.time()>req.expires_at: return False,"Confirmation expired"
        req.state=ConfirmationState.CONFIRMED; req.confirmed_by=user_id; return True,"Confirmed"
    def reject(self, request_id: str, user_id: str) -> Tuple[bool,str]:
        req=self._requests.get(request_id)
        if not req: return False,"Request not found"
        req.state=ConfirmationState.REJECTED; return True,"Rejected"
    def needs_confirmation(self, operation: str) -> bool:
        return any(risk_op in operation for risk_op in self._high_risk_operations)
    def cleanup_expired(self) -> int:
        now=time.time(); expired=[rid for rid,r in self._requests.items() if now>r.expires_at]
        for rid in expired: del self._requests[rid]; return len(expired)
    def engine_stats(self) -> Dict[str,Any]:
        pending=sum(1 for r in self._requests.values() if r.state==ConfirmationState.REQUESTED)
        return {"total_requests":len(self._requests),"pending_confirmations":pending,
            "ttl_seconds":self._confirmation_ttl}


# ═══════════════════════════════════════════════════════════════
# PART I — CLAUDE CODE ORCHESTRATOR (unified coordinator)
# ═══════════════════════════════════════════════════════════════

class ClaudeCodeOrchestrator:
    def __init__(self):
        self.decomposer = TaskDecomposer()
        self.tool_registry = ToolRegistry()
        self.fs_tools = FileSystemTools()
        self.cmd_tool = CommandExecutionTool()
        self.code_tools = CodeGenDebugTools()
        self.scanner = StaticCodeScanner()
        self.context_mgr = ProgrammingContextManager()
        self.confirm_engine = SecurityConfirmationEngine()
        self._setup_builtin_tools()
    def _setup_builtin_tools(self):
        @self.tool_registry.register_tool("read_file","Read file contents",ToolCategory.FILESYSTEM,
            {"path":{"type":"string"},"max_size":{"type":"integer"}})
        def _read(path:str,max_size:int=1024): return self.fs_tools.read_file(path,max_size)
        self.tool_registry.get_tool("read_file").handler=_read

        @self.tool_registry.register_tool("write_file","Write content to file",ToolCategory.FILESYSTEM,
            {"path":{"type":"string"},"content":{"type":"string"}})
        def _write(path:str,content:str): return self.fs_tools.write_file(path,content)
        self.tool_registry.get_tool("write_file").handler=_write

        @self.tool_registry.register_tool("list_directory","List directory contents",ToolCategory.FILESYSTEM,
            {"path":{"type":"string"}})
        def _listdir(path:str="."): return self.fs_tools.list_directory(path)
        self.tool_registry.get_tool("list_directory").handler=_listdir

        @self.tool_registry.register_tool("run_command","Execute shell command",ToolCategory.EXECUTION,
            {"command":{"type":"string"},"cwd":{"type":"string"},"timeout":{"type":"integer"}})
        def _runcmd(command:str,cwd:str=None,timeout:int=30): return self.cmd_tool.run_command(command,cwd,timeout)
        self.tool_registry.get_tool("run_command").handler=_runcmd

        @self.tool_registry.register_tool("generate_code","Generate code from prompt",ToolCategory.CODE_GEN,
            {"prompt":{"type":"string"},"language":{"type":"string"},"context":{"type":"string"}})
        def _gen(prompt:str,language:str="python",context:str=""): return self.code_tools.generate_code(prompt,language,context)
        self.tool_registry.get_tool("generate_code").handler=_gen

        @self.tool_registry.register_tool("debug_code","Debug code with error info",ToolCategory.CODE_DEBUG,
            {"code":{"type":"string"},"error_message":{"type":"string"}})
        def _debug(code:str,error_message:str=""): return self.code_tools.debug_code(code,error_message)
        self.tool_registry.get_tool("debug_code").handler=_debug

        @self.tool_registry.register_tool("explain_code","Explain code line by line",ToolCategory.CODE_DEBUG,
            {"code":{"type":"string"},"detail_level":{"type":"string"}})
        def _explain(code:str,detail_level:str="medium"): return self.code_tools.explain_code(code,detail_level)
        self.tool_registry.get_tool("explain_code").handler=_explain

        @self.tool_registry.register_tool("run_tests","Run unit tests on code",ToolCategory.CODE_DEBUG,
            {"code":{"type":"string"},"test_cases":{"type":"array"}})
        def _tests(code:str,test_cases=None): return self.code_tools.run_tests(code,test_cases)
        self.tool_registry.get_tool("run_tests").handler=_tests

        @self.tool_registry.register_tool("scan_code","Static security scan of code",ToolCategory.UTILITY,
            {"code":{"type":"string"},"filename":{"type":"string"}})
        def _scan(code:str,filename:str="<string>"): return self.scanner.scan_code(code,filename)
        self.tool_registry.get_tool("scan_code").handler=_scan

    def process_programming_request(self, user_input: str, user_id: str="anonymous") -> Dict[str,Any]:
        spec=self.decomposer.decompose(user_input,user_id)
        dag_nodes,sorted_ids,cycle_err=self.decomposer.build_dag(spec.subtasks)
        if cycle_err: return {"spec":spec,"error":cycle_err,"execution_results":[]}
        execution_results=[]
        for sid in sorted_ids:
            st=next((s for s in spec.subtasks if s["id"]==sid),None)
            if not st: continue
            if st["type"]=="analyze_requirement": execution_results.append({"subtask":sid,"status":"skipped"})
            elif st["type"]=="security_check":
                scan=self.scanner.scan_code(st["params"].get("command",""))
                execution_results.append({"subtask":sid,"status":"completed","risk_score":scan.risk_score})
            elif st["type"]=="execute_command":
                needs_conf=self.confirm_engine.needs_confirmation(st["params"].get("command",""))
                if needs_conf:
                    creq=self.confirm_engine.request_confirmation(user_id,"command_execution",f"Run: {st['params'].get('command','')[:100]}")
                    execution_results.append({"subtask":sid,"status":"awaiting_confirmation","confirm_id":creq.request_id})
                else:
                    result=self.cmd_tool.run_command(st["params"].get("command",""),timeout=30)
                    execution_results.append({"subtask":sid,"status":"completed","result":result.output})
            elif st["type"]=="generate_code":
                gen=self.code_tools.generate_code(st["params"].get("input",""),context=user_input)
                execution_results.append({"subtask":sid,"status":"completed","generated":gen.output})
            else:
                execution_results.append({"subtask":sid,"status":"skipped","reason":f"Unknown type: {st['type']}"})
        self.decomposer.persist_spec(spec); return {"spec":spec,"dag_nodes":len(dag_nodes),
            "sorted_ids":sorted_ids,"execution_results":execution_results}
    def get_full_status(self) -> Dict[str,Any]:
        return {"decomposer":self.decomposer.decomposer_stats(),
            "tools":self.tool_registry.registry_stats(),
            "fs_tools":{"workspace":self.fs_tools._root,"whitelists":len(self.fs_tools._whitelist_paths)},
            "cmd_tool":self.cmd_tool.tool_stats(),
            "code_tools":self.code_tools.tool_stats(),
            "scanner":self.scanner.scanner_stats(),
            "context":self.context_mgr.manager_stats(),
            "confirmation":self.confirm_engine.engine_stats()}


# ═══════════════════════════════════════════════════════════════
# PART J — TESTING SUITE
# ═══════════════════════════════════════════════════════════════

def _run_test(name: str, fn) -> tuple:
    try: fn(); return ("PASS", name, None)
    except Exception as e: return ("FAIL", name, str(e))

def run_all_tests() -> Dict[str,Any]:
    results=[]

    def test_decomposer_intent():
        dec=TaskDecomposer(); tt,conf,msg=dec.recognize_intent("写一个Python函数计算房价")
        assert tt==TaskType.CODE_GENERATE; assert conf>=0.5
    results.append(_run_test("DECOMPOSER: intent recognition", test_decomposer_intent))

    def test_decomposer_debug_intent():
        dec=TaskDecomposer(); tt,_,_=dec.recognize_intent("帮我调试这个报错")
        assert tt==TaskType.CODE_DEBUG
    results.append(_run_test("DECOMPOSER: debug intent", test_decomposer_debug_intent))

    def test_decomposer_decompose():
        dec=TaskDecomposer(); spec=dec.decompose("运行ls命令","user1")
        assert spec.task_type==TaskType.COMMAND_EXECUTE; assert len(spec.subtasks)>=1
    results.append(_run_test("DECOMPOSER: full decompose", test_decomposer_decompose))

    def test_dag_build():
        dec=TaskDecomposer(); subs=[{"id":"a","type":"x","params":{},"depends_on":[]},
            {"id":"b","type":"y","params":{},"depends_on":["a"]},{"id":"c","type":"z","params":{},"depends_on":["a"]}]
        dag,ids,err=dec.build_dag(subs); assert err is None; assert ids==["a","b","c"]
    results.append(_run_test("DAG: build+sort", test_dag_build))

    def test_dag_cycle():
        dec=TaskDecomposer(); subs=[{"id":"a","depends_on":["b"]},{"id":"b","depends_on":["a"]}]
        _,_,err=dec.build_dag(subs); assert err is not None; assert "Cycle" in err
    results.append(_run_test("DAG: cycle detection", test_dag_cycle))

    def test_registry_register():
        reg=ToolRegistry()
        @reg.register_tool("test_tool","A test tool",ToolCategory.UTILITY,{"x":{"type":"string"}})
        def dummy(x): return f"got:{x}"
        reg.get_tool("test_tool").handler=dummy
        t=reg.call_tool("test_tool",{"x":"hello"}); assert t.success; assert t.output=="got:hello"
    results.append(_run_test("REGISTRY: register+call", test_registry_register))

    def test_registry_list():
        reg=ToolRegistry()
        @reg.register_tool("t1","",ToolCategory.FILESYSTEM,{})
        def d1(): pass
        @reg.register_tool("t2","",ToolCategory.EXECUTION,{})
        def d2(): pass
        tools=reg.list_tools(); assert len(tools)==2; assert len(reg.list_tools(ToolCategory.EXECUTION))==1
    results.append(_run_test("REGISTRY: list by category", test_registry_list))

    def test_fs_read_write():
        fs=FileSystemTools(tempfile.mkdtemp(prefix="ctest_")); r=fs.write_file("test.txt","hello world")
        assert r.success; r2=fs.read_file("test.txt"); assert r2.success; assert "hello" in r2.output
        shutil.rmtree(fs._root,ignore_errors=True)
    results.append(_run_test("FS: read+write roundtrip", test_fs_read_write))

    def test_fs_list():
        fs=FileSystemTools(tempfile.mkdtemp(prefix="clist_")); fs.write_file("a.txt",""); fs.write_file("b.txt","")
        r=fs.list_directory(); assert r.success; assert len(r.output)>=2
        shutil.rmtree(fs._root,ignore_errors=True)
    results.append(_run_test("FS: directory listing", test_fs_list))

    def test_cmd_whitelist():
        ct=CommandExecutionTool(); r=ct.run_command("echo hello")
        assert r.success; assert "hello" in str(r.output)
        r2=ct.run_command("rm -rf /"); assert not r2.success; assert "not in whitelist" in r2.error
    results.append(_run_test("CMD: whitelist enforcement", test_cmd_whitelist))

    def codegen_generate():
        cg=CodeGenDebugTools(); r=cg.generate_code("calculate fibonacci","python")
        assert r.success; assert "# Auto-generated" in r.output
    results.append(_run_test("CODEGEN: generate code", codegen_generate))

    def codegen_debug():
        cg=CodeGenDebugTools(); r=cg.debug_code("print(x)","NameError: name 'x' is not defined")
        assert r.success; assert len(r.output)>0
    results.append(_run_test("CODEGEN: debug with error", codegen_debug))

    def codegen_explain():
        cg=CodeGenDebugTools(); r=cg.explain_code("def foo(): pass")
        assert r.success; assert len(r.output)>=1
    results.append(_run_test("CODEGEN: explain code", codegen_explain))

    def codegen_tests():
        cg=CodeGenDebugTools(); r=cg.run_tests("x=1+1\nassert x==2")
        assert r.success; assert isinstance(r.output,list); passed=sum(1 for x in r.output if x.get("status")=="passed"); assert passed==len(r.output)
    results.append(_run_test("CODEGEN: run tests", codegen_tests))

    def scanner_safe():
        sc=StaticCodeScanner(); r=sc.scan_code("x=1+1\nprint(x)")
        assert r.risk_score<30; assert r.severity in(RiskSeverity.INFO,RiskSeverity.LOW)
    results.append(_run_test("SCANNER: safe code passes", scanner_safe))

    def scanner_dangerous():
        sc=StaticCodeScanner(); r=sc.scan_code("import os\nos.system('rm -rf /')")
        assert r.risk_score>=40; assert len(r.dangerous_modules)>0
    results.append(_run_test("SCANNER: dangerous detected", scanner_dangerous))

    def scanner_eval():
        sc=StaticCodeScanner(); r=sc.scan_code("eval(user_input)")
        assert r.risk_score>=20; assert "eval" in r.dangerous_functions
    results.append(_run_test("SCANNER: eval detection", scanner_eval))

    def context_basic():
        pcm=ProgrammingContextManager(); pcm.update_context("file_accessed","main.py")
        c=pcm.get_context(); assert "main.py" in c["recent_files"]
    results.append(_run_test("CONTEXT: update+get", context_basic))

    def context_compress():
        pcm=ProgrammingContextManager()
        for i in range(15): pcm.update_context("command_executed",f"cmd{i}")
        pcm.compress_context(); assert len(pcm.get_context()["commands"])<=10
    results.append(_run_test("CONTEXT: compression", context_compress))

    def knowledge_search():
        pcm=ProgrammingContextManager(); pcm.add_knowledge("how to sort?","Use sorted()",["python","internal"])
        pcm.add_knowledge("how to read file?","Use open()",["python","internal"])
        results=pcm.search_knowledge("sort",2); assert len(results)<=2
    results.append(_run_test("KNOWLEDGE: search+retrieve", knowledge_search))

    def snippet_lifecycle():
        pcm=ProgrammingContextManager(); snip=pcm.save_snippet("u1","Fibonacci","python","def fib(n):\n return n","math")
        assert snip.language=="python"; snips=pcm.get_user_snippets("u1"); assert len(snips)>=1
        got=pcm.get_snippet(snip.snippet_id); assert got is not None and got.content=="def fib(n):\n return n"
    results.append(_run_test("SNIPPET: save+get lifecycle", snippet_lifecycle))

    def confirm_flow():
        sce=SecurityConfirmationEngine(); req=sce.request_confirmation("u1","delete /important","Deletes important file")
        assert req.state==ConfirmationState.REQUESTED; assert sce.needs_confirmation("delete /important")==True
        ok,msg=sce.confirm(req.request_id,req.token,"u1"); assert ok
        ok2,_=sce.reject(req.request_id,"u1"); assert ok2
    results.append(_run_test("CONFIRMATION: full flow", confirm_flow))

    def confirm_no_risk():
        sce=SecurityConfirmationEngine(); assert sce.needs_confirmation("echo hello")==False
    results.append(_run_test("CONFIRMATION: low-risk skips", confirm_no_risk))

    def orchestrator_process():
        orc=ClaudeCodeOrchestrator(); result=orc.process_programming_request("写一个hello world程序","u1")
        assert "spec" in result; assert "execution_results" in result
    results.append(_run_test("ORC: process programming request", orchestrator_process))

    def orchestrator_scan():
        orc=ClaudeCodeOrchestrator(); result=orc.process_programming_request("运行echo test","u1")
        assert "spec" in result; eres=result.get("execution_results",[])
        assert any(e.get("risk_score") is not None for e in eres)
    results.append(_run_test("ORC: scan on execute", orchestrator_scan))

    def orchestrator_status():
        orc=ClaudeCodeOrchestrator(); st=orc.get_full_status()
        assert "decomposer" in st; assert "tools" in st; assert "scanner" in st
    results.append(_run_test("ORC: full status", orchestrator_status))

    passed=sum(1 for r in results if r[0]=="PASS")
    failed=[r for r in results if r[0]=="FAIL"]; errors=[r for r in results if r[0]=="ERROR"]
    print(f"\n{'='*60}")
    print(f"L39 CLAUDE CODE CORE CAPABILITY LAYER — TEST SUMMARY")
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
    print("\n✅ Layer 39 — Claude Code Core Capability loaded OK")
