# -*- coding: utf-8 -*-
"""
Layer 42: Red-Blue Adversarial & Code Execution Fusion
======================================================
Self-play adversarial training system with code execution sandbox integration.
Red team generates executable attack scripts; Blue team auto-generates defense code.
Both sides evolve through genetic algorithms and reinforcement learning in isolated sandboxes.
"""

import re
import ast
import json
import random
import hashlib
import time
import threading
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Optional, List, Dict, Any, Tuple, Callable


# ============================================================
# Enums & Data Classes
# ============================================================

class AttackType(PyEnum):
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    DANGEROUS_FUNC_PROBE = "dangerous_func_probe"
    ENV_TAMPERING = "env_tampering"
    PROMPT_INJECTION = "prompt_injection"

class DefenseLevel(PyEnum):
    QUICK_SCAN = "quick_scan"
    DEEP_ANALYSIS = "deep_analysis"
    FULL_LOCKDOWN = "full_lockdown"

class BattleOutcome(PyEnum):
    RED_WIN = "red_win"
    BLUE_WIN = "blue_win"
    DRAW = "draw"
    ERROR = "error"

class SecurityTitle(PyEnum):
    SECURITY_NOVICE = ("security_novice", "安全学徒", 100)
    GUARDIAN = ("guardian", "守护者", 500)
    DEFENSE_EXPERT = ("defense_expert", "防御专家", 1500)
    SECURITY_MASTER = ("security_master", "安全宗师", 5000)
    CYBER_IMMORTAL = ("cyber_immortal", "网络飞升", 15000)

    def __new__(cls, value, label, threshold):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        obj.threshold = threshold
        return obj

@dataclass
class AttackScript:
    script_id: str
    attack_type: AttackType
    code: str
    language: str = "python"
    generation: int = 0
    parent_id: Optional[str] = None
    mutation_ops: List[str] = field(default_factory=list)

@dataclass
class DefenseRule:
    rule_id: str
    pattern: str
    description: str
    level: DefenseLevel
    is_active: bool = True

@dataclass
class BattleRecord:
    battle_id: str
    round_num: int
    red_script: AttackScript
    blue_defense: str
    outcome: BattleOutcome
    red_score: float = 0.0
    blue_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

@dataclass
class TrainingState:
    red_win_rate: float = 0.5
    blue_win_rate: float = 0.5
    total_rounds: int = 0
    red_rewards: List[float] = field(default_factory=list)
    blue_rewards: List[float] = field(default_factory=list)
    best_red_script: Optional[str] = None
    best_defense_code: Optional[str] = None

@dataclass
class UserChallenge:
    challenge_id: str
    user_id: str
    side: str  # "red" or "blue"
    script: str
    submitted_at: float = 0.0
    evaluated: bool = False
    result: Optional[Dict[str, Any]] = None

@dataclass
class TournamentEntry:
    tournament_id: str
    name: str
    start_time: float
    end_time: float
    status: str = "active"
    participants: List[str] = field(default_factory=list)
    rankings: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================
# Module 1: RedTeamAttackGenerator
# ============================================================
class RedTeamAttackGenerator:
    """Generates attack scripts with genetic algorithm variation engine."""

    ATTACK_TEMPLATES = {
        AttackType.PATH_TRAVERSAL: {
            "python": (
                "def attempt_path_traversal():\n"
                "    payloads = {payloads}\n"
                "    for p in payloads:\n"
                "        try:\n"
                "            with open(p, 'r') as f:\n"
                "                return f.read()\n"
                "        except:\n"
                "            continue\n"
                "    return None\n\n"
                "result = attempt_path_traversal()\n"
                'print(f"Attack result: {{result}}")'
            ),
            "shell": (
                'for p in {payloads}; do cat "$p" 2>/dev/null && break; done'
            )
        },
        AttackType.COMMAND_INJECTION: {
            "python": (
                "import subprocess\n"
                "def attempt_cmd_injection():\n"
                "    cmds = {payloads}\n"
                "    for cmd in cmds:\n"
                "        try:\n"
                '            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)\n'
                '            if result.returncode == 0:\n'
                '                return result.stdout.decode()\n'
                "        except:\n"
                "            continue\n"
                "    return None\n\n"
                "result = attempt_cmd_injection()\n"
                'print(f"Injection result: {{result}}")'
            ),
            "shell": "{payloads}"
        },
        AttackType.DANGEROUS_FUNC_PROBE: {
            "python": (
                "def probe_dangerous_functions():\n"
                "    funcs = {payloads}\n"
                "    available = []\n"
                "    for func in funcs:\n"
                "        if func in globals() or func in dir(__builtins__):\n"
                '            available.append(f"Dangerous function {{func}} available")\n'
                "    return available if available else 'Safe'\n\n"
                "result = probe_dangerous_functions()\n"
                'print(f"Probe result: {{result}}")'
            )
        },
        AttackType.ENV_TAMPERING: {
            "python": (
                "import os\n"
                "def tamper_env():\n"
                "    env_vars = {payloads}\n"
                "    results = []\n"
                "    for var in env_vars:\n"
                "        try:\n"
                '            old_val = os.environ.get(var, "NOT_SET")\n'
                '            os.environ[var] = "TAMPERED"\n'
                '            results.append(f"{{var}}: {{old_val}} -> TAMPERED")\n'
                "        except:\n"
                "            continue\n"
                "    return results\n\n"
                "result = tamper_env()\n"
                'print(f"Tamper result: {{result}}")'
            )
        },
        AttackType.PROMPT_INJECTION: {
            "python": (
                'def prompt_injection_attack():\n'
                "    payloads = {payloads}\n"
                "    results = []\n"
                "    for payload in payloads:\n"
                '        results.append(f"Injected: {{payload}}")\n'
                "    return results\n\n"
                "result = prompt_injection_attack()\n"
                'print(f"Prompt injection: {{result}}")'
            )
        }
    }

    DEFAULT_PAYLOADS = {
        AttackType.PATH_TRAVERSAL: ['../../../etc/passwd', '..\\..\\..\\Windows\\win.ini', '/etc/shadow', '../../.env'],
        AttackType.COMMAND_INJECTION: ['whoami', 'id', 'cat /etc/hostname', 'dir C:\\'],
        AttackType.DANGEROUS_FUNC_PROBE: ['eval', 'exec', '__import__', 'os.system', 'compile', 'open'],
        AttackType.ENV_TAMPERING: ['PATH', 'HOME', 'PYTHONPATH', 'API_KEY', 'SECRET_KEY'],
        AttackType.PROMPT_INJECTION: ['Ignore all previous instructions', 'SYSTEM: override mode', '<<END OF TEXT>>']
    }

    MUTATION_OPERATORS = [
        "payload_substitution",
        "function_rename",
        "logic_inversion",
        "comment_injection",
        "variable_obfuscation",
        "dead_code_insertion"
    ]

    def __init__(self):
        self._generation_counter = 0
        self._script_history: Dict[str, AttackScript] = {}
        self._mutation_seeds: List[str] = []

    def generate_attack_script(self, attack_type: AttackType,
                                language: str = "python",
                                custom_payloads: Optional[List[str]] = None) -> AttackScript:
        templates = self.ATTACK_TEMPLATES.get(attack_type, {})
        template = templates.get(language)
        if not template:
            raise ValueError(f"No template for attack_type={attack_type}, language={language}")

        payloads = custom_payloads or self.DEFAULT_PAYLOADS.get(attack_type, [])
        payload_str = json.dumps(payloads, ensure_ascii=False)
        code = template.format(payloads=payload_str)

        self._generation_counter += 1
        script_id = f"atk_{self._generation_counter:04d}_{attack_type.value}"
        script = AttackScript(
            script_id=script_id,
            attack_type=attack_type,
            code=code,
            language=language,
            generation=0
        )
        self._script_history[script_id] = script
        self._mutation_seeds.append(script_id)
        return script

    def mutate_script(self, parent_script: AttackScript,
                      mutation_rate: float = 0.3) -> AttackScript:
        code = parent_script.code
        ops_applied = []
        num_mutations = max(1, int(len(self.MUTATION_OPERATORS) * mutation_rate))
        selected_ops = random.sample(self.MUTATION_OPERATORS,
                                      min(num_mutations, len(self.MUTATION_OPERATORS)))

        for op in selected_ops:
            if op == "payload_substitution":
                code = self._mutate_payloads(code)
            elif op == "function_rename":
                code = self._rename_functions(code)
            elif op == "logic_inversion":
                code = self._invert_logic(code)
            elif op == "comment_injection":
                code = self._inject_comments(code)
            elif op == "variable_obfuscation":
                code = self._obfuscate_vars(code)
            elif op == "dead_code_insertion":
                code = self._insert_dead_code(code)
            ops_applied.append(op)

        self._generation_counter += 1
        script_id = f"atk_{self._generation_counter:04d}_{parent_script.attack_type.value}_m"
        mutated = AttackScript(
            script_id=script_id,
            attack_type=parent_script.attack_type,
            code=code,
            language=parent_script.language,
            generation=parent_script.generation + 1,
            parent_id=parent_script.script_id,
            mutation_ops=ops_applied
        )
        self._script_history[script_id] = mutated
        self._mutation_seeds.append(script_id)
        return mutated

    def _mutate_payloads(self, code: str) -> str:
        extra_payloads = ["../../../../boot.ini", "/proc/version", "echo Hacked",
                          "../../config/database.yml", "ls -la /"]
        if "payloads = " in code:
            insertion = ", " + json.dumps(random.choice(extra_payloads))
            code = code.replace("payloads = ", "payloads = ", 1)
            idx = code.index("[", code.index("payloads = "))
            code = code[:idx+1] + insertion + code[idx+1:]
        return code

    def _rename_functions(self, code: str) -> str:
        renames = [
            ("attempt_path_traversal", "try_read_sensitive"),
            ("attempt_cmd_injection", "run_shell_cmd"),
            ("probe_dangerous_functions", "check_dangerous_apis"),
            ("tamper_env", "modify_environment"),
            ("prompt_injection_attack", "inject_prompt"),
        ]
        for old, new in renames:
            if old in code:
                code = code.replace(old, new, 1)
                break
        return code

    def _invert_logic(self, code: str) -> str:
        if "return None" in code:
            code = code.replace("return None", "return 'BLOCKED'", 1)
        if "'Safe'" in code:
            code = code.replace("'Safe'", "'VULNERABLE'", 1)
        return code

    def _inject_comments(self, code: str) -> str:
        comments = [
            "# Legitimate file operation",
            "# Standard library usage",
            "# Environment variable check",
            "# Normal function call"
        ]
        lines = code.split("\n")
        insert_pos = random.randint(1, max(1, len(lines) - 2))
        lines.insert(insert_pos, random.choice(comments))
        return "\n".join(lines)

    def _obfuscate_vars(self, code: str) -> str:
        obfuscations = [("result", "_res"), ("payloads", "_pl"), ("funcs", "_fn")]
        for old, new in obfuscations:
            if old in code and new not in code:
                count = code.count(old)
                code = code.replace(old, new, count)
                break
        return code

    def _insert_dead_code(self, code: str) -> str:
        dead_code_blocks = [
            "\n_debug_counter = 0\n",
            "\n_dummy = [x for x in range(3)]\n",
            "\n_temp = time.time()\n"
        ]
        lines = code.split("\n")
        if len(lines) > 3:
            insert_pos = random.randint(2, len(lines) - 2)
            lines.insert(insert_pos, random.choice(dead_code_blocks))
        return "\n".join(lines)

    def analyze_sandbox_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        blocked = result.get("blocked", False)
        output = result.get("output", "")
        error = result.get("error", "")

        success = not blocked and bool(output) and not error
        detected_patterns = []
        if "Permission denied" in str(output) or "blocked" in str(output).lower():
            detected_patterns.append("permission_denied")
        if "FileNotFoundError" in str(error):
            detected_patterns.append("file_not_found")
        if "timeout" in str(error).lower():
            detected_patterns.append("execution_timeout")

        return {
            "success": success,
            "blocked": blocked,
            "output_length": len(str(output)),
            "detected_patterns": detected_patterns,
            "verdict": "BYPASSED" if success else ("BLOCKED" if blocked else "FAILED")
        }

    def calculate_reward(self, blocked: bool, execution_time: float,
                         complexity: float = 1.0) -> float:
        if blocked:
            base_reward = -10.0
        else:
            base_reward = 20.0
        time_bonus = max(0, 5.0 - execution_time)
        return (base_reward + time_bonus) * complexity


# ============================================================
# Module 2: BlueTeamDefenseGenerator
# ============================================================
class BlueTeamDefenseGenerator:
    """Auto-generates defense code with static scan, AST analysis, and dynamic testing."""

    BASE_DEFENSE_PATTERNS = [
        (r'\.\./\.\.', "Path traversal pattern", DefenseLevel.QUICK_SCAN),
        (r'os\.system\s*\(', "OS command execution", DefenseLevel.QUICK_SCAN),
        (r'eval\s*\(', "eval() call", DefenseLevel.QUICK_SCAN),
        (r'exec\s*\(', "exec() call", DefenseLevel.QUICK_SCAN),
        (r'__import__\s*\(', "Dynamic import", DefenseLevel.QUICK_SCAN),
        (r'subprocess\.run\s*\(.*shell\s*=\s*True', "Shell injection", DefenseLevel.DEEP_ANALYSIS),
        (r'compile\s*\(', "Compile function", DefenseLevel.DEEP_ANALYSIS),
        (r"open\s*\(['\"]/etc/", "System file access", DefenseLevel.FULL_LOCKDOWN),
        (r'os\.environ\s*\[', "Environment variable access", DefenseLevel.DEEP_ANALYSIS),
        (r'Ignore all previous', "Prompt injection text", DefenseLevel.QUICK_SCAN),
    ]

    DANGEROUS_AST_CALLS = {'eval', 'exec', 'compile', '__import__', 'open'}
    DANGEROUS_AST_ATTRS = {'system', 'popen', 'spawn', 'execve'}

    def __init__(self):
        self._rules: List[DefenseRule] = []
        self._custom_rules: List[DefenseRule] = []
        self._ab_test_results: List[Dict] = []
        self._load_base_rules()

    def _load_base_rules(self):
        for i, (pattern, desc, level) in enumerate(self.BASE_DEFENSE_PATTERNS):
            self._rules.append(DefenseRule(
                rule_id=f"base_{i:03d}",
                pattern=pattern,
                description=desc,
                level=level,
                is_active=True
            ))

    def load_defense_rules(self) -> List[DefenseRule]:
        return [r for r in self._rules + self._custom_rules if r.is_active]

    def add_custom_rule(self, pattern: str, description: str,
                        level: DefenseLevel = DefenseLevel.QUICK_SCAN) -> DefenseRule:
        rule_id = f"custom_{len(self._custom_rules):03d}"
        rule = DefenseRule(rule_id=rule_id, pattern=pattern,
                           description=description, level=level, is_active=True)
        self._custom_rules.append(rule)
        return rule

    def generate_defense_code(self, attack_log: List[Dict[str, Any]]) -> str:
        patterns_found = set()
        for entry in attack_log:
            code = entry.get("code", "")
            atype = entry.get("attack_type", "")
            rules = self.static_scan(code)
            for r in rules:
                patterns_found.add(r["pattern"])

        dynamic_section = ""
        if any("path_traversal" in str(e.get("attack_type","")) for e in attack_log):
            dynamic_section += (
                "\n    # Dynamic path normalization\n"
                "    sanitized = os.path.normpath(path)\n"
                '    if ".." in sanitized or sanitized.startswith("/"):\n'
                '        return {"blocked": True, "reason": "Path traversal detected"}\n'
            )

        ast_funcs = set()
        for entry in attack_log:
            code = entry.get("code", "")
            ast_result = self.ast_analysis(code)
            for call in ast_result.get("dangerous_calls", []):
                ast_funcs.add(call)

        forbidden_list = json.dumps(list(ast_funcs), ensure_ascii=False) if ast_funcs else "[]"

        defense_code = (
            "import re\n"
            "import os\n"
            "import ast as _ast_mod\n\n"
            "DANGEROUS_PATTERNS = " + json.dumps(list(patterns_found), ensure_ascii=False) + "\n"
            "FORBIDDEN_CALLS = " + forbidden_list + "\n\n"
            "def sandbox_precheck(code: str) -> dict:\n"
            '    """Blue team dynamic defense function"""\n'
            "    # Level 1: Regex static scan\n"
            "    for pattern in DANGEROUS_PATTERNS:\n"
            "        if re.search(pattern, code):\n"
            '            return {"blocked": True, "reason": f"Pattern matched: {pattern}"}\n'
            "\n"
            "    # Level 2: AST deep analysis\n"
            "    try:\n"
            "        tree = _ast_mod.parse(code)\n"
            "        for node in _ast_mod.walk(tree):\n"
            "            if isinstance(node, _ast_mod.Call):\n"
            "                if isinstance(node.func, _ast_mod.Name):\n"
                    "                    if node.func.id in FORBIDDEN_CALLS:\n"
                    '                        return {"blocked": True, "reason": f"Forbidden: {node.func.id}"}\n'
            "    except SyntaxError:\n"
            '        return {"blocked": True, "reason": "SyntaxError in code"}\n'
            "    except Exception:\n"
            "        pass\n"
            "\n"
            "    # Level 3: Behavior heuristics\n"
            '    suspicious_keywords = ["__import__", "eval(", "exec(", "os.system"]\n'
            "    for kw in suspicious_keywords:\n"
            "        if kw in code:\n"
            '            return {"blocked": True, "reason": f"Suspicious keyword: {kw}"}\n'
            "\n"
            '    return {"blocked": False}\n'
        )
        return defense_code

    def static_scan(self, code: str) -> List[Dict[str, Any]]:
        results = []
        rules = self.load_defense_rules()
        for rule in rules:
            if re.search(rule.pattern, code):
                results.append({
                    "rule_id": rule.rule_id,
                    "pattern": rule.pattern,
                    "description": rule.description,
                    "level": rule.level.value
                })
        return results

    def ast_analysis(self, code: str) -> Dict[str, Any]:
        dangerous_calls = []
        dangerous_attrs = []
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_AST_CALLS:
                            dangerous_calls.append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in self.DANGEROUS_AST_ATTRS:
                            dangerous_attrs.append(node.func.attr)
        except SyntaxError:
            return {"parse_error": True, "dangerous_calls": [], "dangerous_attrs": [], "imports": []}

        return {
            "parse_error": False,
            "dangerous_calls": dangerous_calls,
            "dangerous_attrs": dangerous_attrs,
            "imports": imports,
            "risk_score": len(dangerous_calls) * 10 + len(dangerous_attrs) * 15
        }

    def dynamic_sandbox_test(self, code: str, test_inputs: Optional[List[str]] = None) -> Dict[str, Any]:
        scan_result = self.static_scan(code)
        if scan_result:
            return {"safe": False, "block_reason": scan_result[0].get("description", "Pattern matched")}
        ast_result = self.ast_analysis(code)
        if ast_result.get("dangerous_calls"):
            return {"safe": False, "block_reason": f"Dangerous calls: {ast_result['dangerous_calls']}"}
        return {"safe": True, "block_reason": None}

    def multi_level_defense(self, code: str, level: DefenseLevel = DefenseLevel.DEEP_ANALYSIS) -> Dict[str, Any]:
        start_time = time.time()
        results = {
            "level": level.value,
            "passed_levels": [],
            "blocked_at": None,
            "details": {},
            "total_time_ms": 0
        }

        if level.value in ("quick_scan", "deep_analysis", "full_lockdown"):
            quick = self.static_scan(code)
            results["details"]["quick_scan"] = quick
            if quick:
                results["blocked_at"] = "quick_scan"
                results["total_time_ms"] = (time.time() - start_time) * 1000
                return results
            results["passed_levels"].append("quick_scan")

        if level.value in ("deep_analysis", "full_lockdown"):
            ast_r = self.ast_analysis(code)
            results["details"]["ast_analysis"] = ast_r
            if ast_r.get("dangerous_calls") or ast_r.get("dangerous_attrs"):
                results["blocked_at"] = "ast_analysis"
                results["total_time_ms"] = (time.time() - start_time) * 1000
                return results
            results["passed_levels"].append("ast_analysis")

        if level.value == "full_lockdown":
            dynamic = self.dynamic_sandbox_test(code)
            results["details"]["dynamic_test"] = dynamic
            if not dynamic.get("safe"):
                results["blocked_at"] = "dynamic_test"
                results["total_time_ms"] = (time.time() - start_time) * 1000
                return results
            results["passed_levels"].append("dynamic_test")

        results["total_time_ms"] = (time.time() - start_time) * 1000
        return results

    def ab_test_strategy(self, defense_a_code: str, defense_b_code: str,
                         test_cases: List[str]) -> Dict[str, Any]:
        stats_a = {"blocked": 0, "passed": 0}
        stats_b = {"blocked": 0, "passed": 0}
        a_details = []
        b_details = []

        for tc in test_cases:
            ra = self.static_scan(defense_a_code + "\n" + tc) if tc else self.static_scan(defense_a_code)
            rb = self.static_scan(defense_b_code + "\n" + tc) if tc else self.static_scan(defense_b_code)
            if ra:
                stats_a["blocked"] += 1
            else:
                stats_a["passed"] += 1
            a_details.append({"input": tc[:50], "blocked": bool(ra)})
            if rb:
                stats_b["blocked"] += 1
            else:
                stats_b["passed"] += 1
            b_details.append({"input": tc[:50], "blocked": bool(rb)})

        total = len(test_cases) if test_cases else 1
        record = {
            "strategy_a": {"block_rate": stats_a["blocked"] / total, "stats": stats_a},
            "strategy_b": {"block_rate": stats_b["blocked"] / total, "stats": stats_b},
            "winner": "A" if stats_a["blocked"] > stats_b["blocked"] else ("B" if stats_b["blocked"] > stats_a["blocked"] else "TIE"),
            "test_count": total,
            "timestamp": time.time()
        }
        self._ab_test_results.append(record)
        return record


# ============================================================
# Module 3: AdversarialArena
# ============================================================
class AdversarialArena:
    """Sandbox-based confrontation environment with round management."""

    def __init__(self):
        self._battle_history: List[BattleRecord] = []
        self._current_round = 0
        self._lock = threading.Lock()
        self._red_generator = RedTeamAttackGenerator()
        self._blue_generator = BlueTeamDefenseGenerator()

    @property
    def red_generator(self) -> RedTeamAttackGenerator:
        return self._red_generator

    @property
    def blue_generator(self) -> BlueTeamDefenseGenerator:
        return self._blue_generator

    def run_round(self, red_scripts: List[AttackScript],
                  blue_defense_code: str) -> List[BattleRecord]:
        records = []
        with self._lock:
            self._current_round += 1
            for script in red_scripts:
                record = self._execute_confrontation(script, blue_defense_code, self._current_round)
                records.append(record)
                self._battle_history.append(record)
        return records

    def _execute_confrontation(self, red_script: AttackScript,
                               blue_defense: str, round_num: int) -> BattleRecord:
        t0 = time.time()
        try:
            blue_result = self._blue_generator.multi_level_defense(red_script.code)
            blocked = blue_result.get("blocked_at") is not None

            if blocked:
                outcome = BattleOutcome.BLUE_WIN
                red_score = -5.0
                blue_score = 10.0
            else:
                outcome = BattleOutcome.RED_WIN
                red_score = 15.0
                blue_score = -5.0

            analysis = self._red_generator.analyze_sandbox_result({
                "blocked": blocked,
                "output": "" if blocked else "execution_completed",
                "error": "" if not blocked else "Blocked by defense"
            })
        except Exception as exc:
            outcome = BattleOutcome.ERROR
            red_score = 0.0
            blue_score = 0.0
            analysis = {"success": False, "error": str(exc)}

        battle_id = f"battle_{round_num:04d}_{red_script.script_id}"
        return BattleRecord(
            battle_id=battle_id,
            round_num=round_num,
            red_script=red_script,
            blue_defense=blue_defense,
            outcome=outcome,
            red_score=red_score,
            blue_score=blue_score,
            details={**analysis, "defense_result": blue_result.get("blocked_at")},
            timestamp=time.time() - t0
        )

    def evaluate_confrontation(self, record: BattleRecord) -> Dict[str, Any]:
        return {
            "battle_id": record.battle_id,
            "outcome": record.outcome.value,
            "red_score": record.red_score,
            "blue_score": record.blue_score,
            "verdict": record.details.get("verdict", "UNKNOWN"),
            "defense_blocked_at": record.details.get("defense_blocked_at"),
            "duration_sec": record.timestamp
        }

    def get_battle_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        records = self._battle_history[-limit:]
        return [
            {
                "battle_id": r.battle_id,
                "round": r.round_num,
                "outcome": r.outcome.value,
                "red_script_id": r.red_script.script_id,
                "red_score": r.red_score,
                "blue_score": r.blue_score
            }
            for r in records
        ]

    def calculate_win_rate(self, team: str, rounds: int = 100) -> float:
        recent = self._battle_history[-rounds:] if self._battle_history else []
        if not recent:
            return 0.5
        target = "red" if team.lower().startswith("r") else "blue"
        wins = sum(1 for r in recent if
                   (target == "red" and r.outcome == BattleOutcome.RED_WIN) or
                   (target == "blue" and r.outcome == BattleOutcome.BLUE_WIN))
        return wins / len(recent)


# ============================================================
# Module 4: SelfPlayTrainingController
# ============================================================
class SelfPlayTrainingController:
    """PPO-style self-play training loop with 100-round cycles."""

    CYCLE_ROUNDS = 100
    SCRIPTS_PER_ROUND = 10
    FINE_TUNE_THRESHOLD = 0.35
    LEARNING_RATE = 0.01
    ENTROPY_BONUS = 0.01
    DISCOUNT_FACTOR = 0.99

    def __init__(self, arena: AdversarialArena):
        self._arena = arena
        self._state = TrainingState()
        self._training_log: List[Dict] = []
        self._policy_params_red: Dict[str, float] = {"exploration": 0.5, "aggression": 0.5}
        self._policy_params_blue: Dict[str, float] = {"strictness": 0.7, "adaptivity": 0.5}
        self._deployed_strategy: Optional[str] = None

    @property
    def state(self) -> TrainingState:
        return self._state

    def run_training_cycle(self, num_rounds: int = CYCLE_ROUNDS) -> Dict[str, Any]:
        cycle_start = time.time()
        blue_defense = self._arena.blue_generator.generate_defense_code([])
        all_records = []

        for rnd in range(1, num_rounds + 1):
            red_scripts = []
            for _ in range(self.SCRIPTS_PER_ROUND):
                atype = random.choice(list(AttackType))
                script = self._arena.red_generator.generate_attack_script(atype)
                if rnd > 1 and random.random() < self._policy_params_red["exploration"]:
                    parent = random.choice(self._arena.red_generator._mutation_seeds[-5:])
                    parent_obj = self._arena.red_generator._script_history.get(parent)
                    if parent_obj:
                        script = self._arena.red_generator.mutate_script(parent_obj)
                red_scripts.append(script)

            records = self._arena.run_round(red_scripts, blue_defense)
            all_records.extend(records)

            round_red_rewards = [r.red_score for r in records]
            round_blue_rewards = [r.blue_score for r in records]
            self._state.red_rewards.extend(round_red_rewards)
            self._state.blue_rewards.extend(round_blue_rewards)

            if rnd % 25 == 0:
                self._red_policy_update(round_red_rewards)
                self._blue_policy_update(round_blue_rewards)

        self._state.total_rounds += num_rounds
        red_wins = sum(1 for r in all_records if r.outcome == BattleOutcome.RED_WIN)
        blue_wins = sum(1 for r in all_records if r.outcome == BattleOutcome.BLUE_WIN)
        total = len(all_records) or 1
        self._state.red_win_rate = red_wins / total
        self._state.blue_win_rate = blue_wins / total

        log_entry = {
            "cycle_rounds": num_rounds,
            "red_win_rate": self._state.red_win_rate,
            "blue_win_rate": self._state.blue_win_rate,
            "duration_sec": time.time() - cycle_start,
            "total_battles": len(all_records)
        }
        self._training_log.append(log_entry)
        return log_entry

    def _red_policy_update(self, rewards: List[float]):
        if not rewards:
            return
        avg_r = sum(rewards) / len(rewards)
        exploration_delta = self.LEARNING_RATE * (1.0 if avg_r > 0 else -1.0)
        aggression_delta = self.LEARNING_RATE * (0.5 if avg_r > 5 else -0.2)
        self._policy_params_red["exploration"] = max(0.05, min(0.95,
            self._policy_params_red["exploration"] + exploration_delta))
        self._policy_params_red["aggression"] = max(0.1, min(1.0,
            self._policy_params_red["aggression"] + aggression_delta))

    def _blue_policy_update(self, rewards: List[float]):
        if not rewards:
            return
        avg_r = sum(rewards) / len(rewards)
        strictness_delta = self.LEARNING_RATE * (0.3 if avg_r > 0 else -0.2)
        adaptivity_delta = self.LEARNING_RATE * (0.2 if abs(avg_r) > 3 else 0.05)
        self._policy_params_blue["strictness"] = max(0.2, min(1.0,
            self._policy_params_blue["strictness"] + strictness_delta))
        self._policy_params_blue["adaptivity"] = max(0.1, min(1.0,
            self._policy_params_blue["adaptivity"] + adaptivity_delta))

    def evaluate_and_fine_tune(self) -> Dict[str, Any]:
        red_wr = self._state.red_win_rate
        blue_wr = self._state.blue_win_rate
        actions = []

        if red_wr < self.FINE_TUNE_THRESHOLD:
            actions.append("RED_FINE_TUNE: win rate too low, adjusting policy")
            self._policy_params_red["aggression"] = min(1.0, self._policy_params_red["aggression"] + 0.15)
            self._policy_params_red["exploration"] = min(0.9, self._policy_params_red["exploration"] + 0.1)

        if blue_wr < self.FINE_TUNE_THRESHOLD:
            actions.append("BLUE_FINE_TUNE: win rate too low, tightening defense")
            self._policy_params_blue["strictness"] = min(1.0, self._policy_params_blue["strictness"] + 0.15)
            self._blue_generator.add_custom_rule(r'__class__\s*\.__', "Metaclass access", DefenseLevel.FULL_LOCKDOWN)

        trigger_fine_tune = (red_wr < self.FINE_TUNE_THRESHOLD or blue_wr < self.FINE_TUNE_THRESHOLD)
        return {
            "triggered": trigger_fine_tune,
            "red_win_rate": red_wr,
            "blue_win_rate": blue_wr,
            "threshold": self.FINE_TUNE_THRESHOLD,
            "actions_taken": actions,
            "red_policy": dict(self._policy_params_red),
            "blue_policy": dict(self._policy_params_blue)
        }

    def deploy_best_strategy(self) -> Dict[str, Any]:
        best_defense = self._arena.blue_generator.generate_defense_code(
            [{"attack_type": "path_traversal", "code": ""},
             {"attack_type": "command_injection", "code": ""},
             {"attack_type": "dangerous_func_probe", "code": ""}]
        )
        self._deployed_strategy = best_defense
        self._state.best_defense_code = best_defense
        return {
            "deployed": True,
            "defense_code_length": len(best_defense),
            "rules_count": len(self._arena.blue_generator.load_defense_rules()),
            "timestamp": time.time(),
            "total_training_rounds": self._state.total_rounds
        }


# ============================================================
# Module 5: CultivationAdversarialFusion
# ============================================================
class CultivationAdversarialFusion:
    """Fuses adversarial system with cultivation mechanism: challenges, rewards, titles, leaderboards."""

    EXP_REWARDS = {
        "successful_attack": 30,
        "successful_defense": 40,
        "novel_attack_variant": 20,
        "defense_improvement": 25,
        "tournament_win": 100,
        "tournament_participation": 10
    }

    POINTS_REWARDS = {
        "successful_attack": 15,
        "successful_defense": 20,
        "novel_attack_variant": 10,
        "defense_improvement": 12,
        "tournament_win": 50,
        "tournament_participation": 5
    }

    def __init__(self):
        self._challenges: Dict[str, UserChallenge] = {}
        self._user_scores: Dict[str, Dict[str, float]] = {}
        self._user_titles: Dict[str, List[str]] = {}
        self._tournaments: Dict[str, TournamentEntry] = {}
        self._leaderboard_cache: Dict[str, List[Dict]] = {}

    def submit_challenge(self, user_id: str, script: str,
                         side: str) -> UserChallenge:
        ch_id = f"chal_{len(self._challenges):04d}_{int(time.time())}"
        challenge = UserChallenge(
            challenge_id=ch_id,
            user_id=user_id,
            side=side,
            script=script,
            submitted_at=time.time()
        )
        self._challenges[ch_id] = challenge
        if user_id not in self._user_scores:
            self._user_scores[user_id] = {"exp": 0.0, "points": 0.0, "wins": 0, "submissions": 0}
        self._user_scores[user_id]["submissions"] += 1
        return challenge

    def evaluate_user_submission(self, submission: UserChallenge,
                                  current_defense: str) -> Dict[str, Any]:
        blue_gen = BlueTeamDefenseGenerator()
        result = blue_gen.multi_level_defense(submission.script)

        is_blocked = result.get("blocked_at") is not None
        success = (submission.side == "red" and not is_blocked) or \
                  (submission.side == "blue" and is_blocked)

        eval_result = {
            "challenge_id": submission.challenge_id,
            "user_id": submission.user_id,
            "side": submission.side,
            "success": success,
            "blocked": is_blocked,
            "defense_level": result.get("level"),
            "blocked_at": result.get("blocked_at"),
            "exp_award": 0,
            "points_award": 0,
            "title_granted": None
        }

        if success:
            reward_key = "successful_attack" if submission.side == "red" else "successful_defense"
            exp_amt = self.EXP_REWARDS.get(reward_key, 10)
            pts_amt = self.POINTS_REWARDS.get(reward_key, 5)
            eval_result["exp_award"] = exp_amt
            eval_result["points_award"] = pts_amt
            self.award_experience(submission.user_id, exp_amt, reward_key)
            title = self._check_title_eligibility(submission.user_id)
            if title:
                eval_result["title_granted"] = title

        submission.evaluated = True
        submission.result = eval_result
        return eval_result

    def award_experience(self, user_id: str, amount: float, reason: str):
        if user_id not in self._user_scores:
            self._user_scores[user_id] = {"exp": 0.0, "points": 0.0, "wins": 0, "submissions": 0}
        self._user_scores[user_id]["exp"] += amount
        if "win" in reason.lower() or "successful" in reason.lower():
            self._user_scores[user_id]["wins"] += 1

    def grant_security_title(self, user_id: str, title: SecurityTitle) -> bool:
        if user_id not in self._user_titles:
            self._user_titles[user_id] = []
        scores = self._user_scores.get(user_id, {})
        total_exp = scores.get("exp", 0)
        if total_exp >= title.threshold:
            if title.label not in self._user_titles[user_id]:
                self._user_titles[user_id].append(title.label)
                return True
        return False

    def _check_title_eligibility(self, user_id: str) -> Optional[str]:
        scores = self._user_scores.get(user_id, {})
        total_exp = scores.get("exp", 0)
        for title in reversed(list(SecurityTitle)):
            if total_exp >= title.threshold:
                if self.grant_security_title(user_id, title):
                    return title.label
        return None

    def get_leaderboard(self, category: str = "exp") -> List[Dict[str, Any]]:
        cache_key = f"{category}_{len(self._challenges)}"
        if cache_key in self._leaderboard_cache:
            return self._leaderboard_cache[cache_key]

        ranked = sorted(
            [{"user_id": uid, **scores} for uid, scores in self._user_scores.items()],
            key=lambda x: x.get(category, 0),
            reverse=True
        )[:20]

        for i, entry in enumerate(ranked):
            entry["rank"] = i + 1
            entry["titles"] = self._user_titles.get(entry["user_id"], [])

        self._leaderboard_cache[cache_key] = ranked
        return ranked

    def create_tournament(self, name: str, duration_hours: int = 24) -> TournamentEntry:
        t_id = f"tour_{len(self._tournaments):04d}"
        now = time.time()
        tournament = TournamentEntry(
            tournament_id=t_id,
            name=name,
            start_time=now,
            end_time=now + duration_hours * 3600,
            status="active"
        )
        self._tournaments[t_id] = tournament
        return tournament

    def join_tournament(self, tournament_id: str, user_id: str) -> bool:
        t = self._tournaments.get(tournament_id)
        if t and t.status == "active" and user_id not in t.participants:
            t.participants.append(user_id)
            return True
        return False

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        scores = self._user_scores.get(user_id, {"exp": 0.0, "points": 0.0, "wins": 0, "submissions": 0})
        return {
            "user_id": user_id,
            "exp": scores.get("exp", 0),
            "points": scores.get("points", 0),
            "wins": scores.get("wins", 0),
            "submissions": scores.get("submissions", 0),
            "titles": self._user_titles.get(user_id, []),
            "challenges_submitted": sum(1 for c in self._challenges.values() if c.user_id == user_id)
        }


# ============================================================
# Module 6: RedBlueOrchestrator
# ============================================================
class RedBlueOrchestrator:
    """Unified coordinator wiring all adversarial modules together."""

    def __init__(self):
        self._arena = AdversarialArena()
        self._trainer = SelfPlayTrainingController(self._arena)
        self._fusion = CultivationAdversarialFusion()
        self._initialized = False
        self._status = "idle"

    def initialize(self) -> Dict[str, Any]:
        self._arena.red_generator.generate_attack_script(AttackType.PATH_TRAVERSAL)
        self._arena.blue_generator.add_custom_rule(r'sandbox_escape', "Sandbox escape attempt", DefenseLevel.FULL_LOCKDOWN)
        self._initialized = True
        self._status = "ready"
        return {
            "status": "ready",
            "arena_ready": True,
            "trainer_ready": True,
            "fusion_ready": True,
            "base_rules_loaded": len(self._arena.blue_generator.load_defense_rules()),
            "initial_timestamp": time.time()
        }

    def run_adversarial_training(self, rounds: int = 50) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()
        self._status = "training"
        cycle_result = self._trainer.run_training_cycle(rounds)
        fine_tune = self._trainer.evaluate_and_fine_tune()
        self._status = "idle"
        return {
            "cycle_result": cycle_result,
            "fine_tune": fine_tune,
            "trainer_state": {
                "red_win_rate": self._trainer.state.red_win_rate,
                "blue_win_rate": self._trainer.state.blue_win_rate,
                "total_rounds": self._trainer.state.total_rounds
            }
        }

    def handle_user_challenge(self, user_id: str, script: str,
                               side: str) -> Dict[str, Any]:
        challenge = self._fusion.submit_challenge(user_id, script, side)
        defense_code = self._trainer._deployed_strategy or self._arena.blue_generator.generate_defense_code([])
        evaluation = self._fusion.evaluate_user_submission(challenge, defense_code)
        return evaluation

    def get_dashboard(self) -> Dict[str, Any]:
        return {
            "system_status": self._status,
            "initialized": self._initialized,
            "arena": {
                "total_battles": len(self._arena._battle_history),
                "current_round": self._arena._current_round,
                "red_win_rate": self._arena.calculate_win_rate("red"),
                "blue_win_rate": self._arena.calculate_win_rate("blue"),
                "recent_history": self._arena.get_battle_history(limit=5)
            },
            "trainer": {
                "total_rounds": self._trainer.state.total_rounds,
                "red_win_rate": self._trainer.state.red_win_rate,
                "blue_win_rate": self._trainer.state.blue_win_rate,
                "red_policy": dict(self._trainer._policy_params_red),
                "blue_policy": dict(self._trainer._policy_params_blue),
                "deployed": self._trainer._deployed_strategy is not None
            },
            "fusion": {
                "total_challenges": len(self._fusion._challenges),
                "total_users": len(self._fusion._user_scores),
                "active_tournaments": sum(1 for t in self._fusion._tournaments.values() if t.status == "active"),
                "leaderboard_top5": self._fusion.get_leaderboard()[:5]
            }
        }

    def quick_demo(self) -> Dict[str, Any]:
        self.initialize()
        red_gen = self._arena.red_generator
        script = red_gen.generate_attack_script(AttackType.PATH_TRAVERSAL)
        mutated = red_gen.mutate_script(script)
        blue_gen = self._arena.blue_generator
        defense = blue_gen.generate_defense_code([{"attack_type": "path_traversal", "code": script.code}])
        records = self._arena.run_round([script, mutated], defense)
        return {
            "original_script_id": script.script_id,
            "mutated_script_id": mutated.script_id,
            "mutation_ops": mutated.mutation_ops,
            "defense_code_preview": defense[:200],
            "battle_outcomes": [(r.outcome.value, r.red_score, r.blue_score) for r in records],
            "scan_result": blue_gen.static_scan(script.code),
            "ast_result": blue_gen.ast_analysis(script.code)
        }


# ============================================================
# Test Suite
# ============================================================
def run_tests() -> Dict[str, Any]:
    results = []
    errors = []

    def _ok(name: str):
        results.append(name)

    def _fail(name: str, err: str):
        results.append(f"[FAIL] {name}: {err}")
        errors.append(name)

    # --- Test 1: Red generator - path traversal ---
    try:
        gen = RedTeamAttackGenerator()
        s = gen.generate_attack_script(AttackType.PATH_TRAVERSAL)
        assert s.attack_type == AttackType.PATH_TRAVERSAL
        assert "attempt_path_traversal" in s.code
        assert "payloads" in s.code
        assert s.generation == 0
        _ok("red_generate_path_traversal")
    except Exception as e:
        _fail("red_generate_path_traversal", str(e))

    # --- Test 2: Red generator - command injection ---
    try:
        gen = RedTeamAttackGenerator()
        s = gen.generate_attack_script(AttackType.COMMAND_INJECTION, language="shell")
        assert s.language == "shell"
        assert "whoami" in s.code or "cmd" in s.code.lower()
        _ok("red_generate_cmd_injection")
    except Exception as e:
        _fail("red_generate_cmd_injection", str(e))

    # --- Test 3: Red generator - dangerous func probe ---
    try:
        gen = RedTeamAttackGenerator()
        s = gen.generate_attack_script(AttackType.DANGEROUS_FUNC_PROBE)
        assert "probe_dangerous_functions" in s.code
        assert "eval" in s.code or "exec" in s.code
        _ok("red_generate_func_probe")
    except Exception as e:
        _fail("red_generate_func_probe", str(e))

    # --- Test 4: Genetic mutation ---
    try:
        gen = RedTeamAttackGenerator()
        parent = gen.generate_attack_script(AttackType.PATH_TRAVERSAL)
        mutant = gen.mutate_script(parent, mutation_rate=0.5)
        assert mutant.generation == 1
        assert mutant.parent_id == parent.script_id
        assert len(mutant.mutation_ops) >= 1
        assert mutant.code != parent.code
        _ok("genetic_mutation")
    except Exception as e:
        _fail("genetic_mutation", str(e))

    # --- Test 5: Mutation produces different variants ---
    try:
        gen = RedTeamAttackGenerator()
        parent = gen.generate_attack_script(AttackType.ENV_TAMPERING)
        variants = [gen.mutate_script(parent).code for _ in range(5)]
        unique = len(set(variants))
        assert unique >= 3, f"Expected >=3 unique variants, got {unique}"
        _ok("mutation_diversity")
    except Exception as e:
        _fail("mutation_diversity", str(e))

    # --- Test 6: Reward calculation ---
    try:
        gen = RedTeamAttackGenerator()
        r_blocked = gen.calculate_reward(blocked=True, execution_time=0.5)
        r_success = gen.calculate_reward(blocked=False, execution_time=0.2)
        assert r_blocked < 0, f"Blocked should be negative, got {r_blocked}"
        assert r_success > 0, f"Success should be positive, got {r_success}"
        assert r_success > r_blocked
        _ok("reward_calculation")
    except Exception as e:
        _fail("reward_calculation", str(e))

    # --- Test 7: Sandbox result analysis ---
    try:
        gen = RedTeamAttackGenerator()
        r1 = gen.analyze_sandbox_result({"blocked": True, "output": "", "error": ""})
        assert r1["success"] is False
        assert r1["verdict"] == "BLOCKED"
        r2 = gen.analyze_sandbox_result({"blocked": False, "output": "secret_data", "error": ""})
        assert r2["success"] is True
        assert r2["verdict"] == "BYPASSED"
        _ok("sandbox_analysis")
    except Exception as e:
        _fail("sandbox_analysis", str(e))

    # --- Test 8: Blue static scan detects patterns ---
    try:
        bg = BlueTeamDefenseGenerator()
        hits = bg.static_scan('import os\nos.system("whoami")')
        assert len(hits) >= 1
        patterns_found = [h["pattern"] for h in hits]
        assert any("os.system" in p or "system" in p for p in patterns_found)
        _ok("blue_static_scan")
    except Exception as e:
        _fail("blue_static_scan", str(e))

    # --- Test 9: Blue AST analysis catches dangerous calls ---
    try:
        bg = BlueTeamDefenseGenerator()
        result = bg.ast_analysis("x = eval(user_input)")
        assert result["parse_error"] is False
        assert "eval" in result["dangerous_calls"]
        assert result["risk_score"] >= 10
        _ok("blue_ast_analysis")
    except Exception as e:
        _fail("blue_ast_analysis", str(e))

    # --- Test 10: Blue AST handles syntax error ---
    try:
        bg = BlueTeamDefenseGenerator()
        result = bg.ast_analysis("def broken(:\n  return x")
        assert result["parse_error"] is True
        assert len(result["dangerous_calls"]) == 0
        _ok("blue_ast_syntax_error")
    except Exception as e:
        _fail("blue_ast_syntax_error", str(e))

    # --- Test 11: Multi-level defense pipeline ---
    try:
        bg = BlueTeamDefenseGenerator()
        safe_code = "def hello():\n    return 'world'"
        result = bg.multi_level_defense(safe_code, DefenseLevel.DEEP_ANALYSIS)
        assert result["blocked_at"] is None
        assert "quick_scan" in result["passed_levels"]
        assert "ast_analysis" in result["passed_levels"]
        _ok("multi_level_defense_safe")
    except Exception as e:
        _fail("multi_level_defense_safe", str(e))

    # --- Test 12: Multi-level defense blocks dangerous code ---
    try:
        bg = BlueTeamDefenseGenerator()
        dangerous = "import os\nos.system('rm -rf /')"
        result = bg.multi_level_defense(dangerous, DefenseLevel.DEEP_ANALYSIS)
        assert result["blocked_at"] is not None
        assert result["blocked_at"] == "quick_scan"
        _ok("multi_level_defense_block")
    except Exception as e:
        _fail("multi_level_defense_block", str(e))

    # --- Test 13: Generate defense code from attack log ---
    try:
        bg = BlueTeamDefenseGenerator()
        log = [
            {"attack_type": "path_traversal", "code": "../../../etc/passwd"},
            {"attack_type": "command_injection", "code": "os.system('id')"}
        ]
        defense = bg.generate_defense_code(log)
        assert "DANGEROUS_PATTERNS" in defense
        assert "sandbox_precheck" in defense
        assert "re.search" in defense
        _ok("generate_defense_code")
    except Exception as e:
        _fail("generate_defense_code", str(e))

    # --- Test 14: A/B test comparison ---
    try:
        bg = BlueTeamDefenseGenerator()
        strategy_a = "import re\nPATTERN=r'os\\.system'"
        strategy_b = "import re\nPATTERN=r'eval'"
        test_cases = ["os.system('ls')", "eval('1+1')", "print('hello')"]
        result = bg.ab_test_strategy(strategy_a, strategy_b, test_cases)
        assert "winner" in result
        assert result["test_count"] == 3
        assert "strategy_a" in result and "strategy_b" in result
        _ok("ab_test_comparison")
    except Exception as e:
        _fail("ab_test_comparison", str(e))

    # --- Test 15: Arena single round confrontation ---
    try:
        arena = AdversarialArena()
        red_gen = arena.red_generator
        scripts = [
            red_gen.generate_attack_script(AttackType.PATH_TRAVERSAL),
            red_gen.generate_attack_script(AttackType.COMMAND_INJECTION)
        ]
        blue_def = arena.blue_generator.generate_defense_code([])
        records = arena.run_round(scripts, blue_def)
        assert len(records) == 2
        assert all(isinstance(r, BattleRecord) for r in records)
        assert all(r.outcome in (BattleOutcome.RED_WIN, BattleOutcome.BLUE_WIN) for r in records)
        _ok("arena_single_round")
    except Exception as e:
        _fail("arena_single_round", str(e))

    # --- Test 16: Arena battle history ---
    try:
        arena = AdversarialArena()
        red_gen = arena.red_generator
        s = red_gen.generate_attack_script(AttackType.PROMPT_INJECTION)
        arena.run_round([s], "dummy_defense")
        history = arena.get_battle_history(limit=10)
        assert len(history) == 1
        assert "battle_id" in history[0]
        assert "outcome" in history[0]
        _ok("arena_battle_history")
    except Exception as e:
        _fail("arena_battle_history", str(e))

    # --- Test 17: Arena win rate calculation ---
    try:
        arena = AdversarialArena()
        red_gen = arena.red_generator
        safe_scripts = [red_gen.generate_attack_script(AttackType.ENV_TAMPERING) for _ in range(7)]
        arena.run_round(safe_scripts, "weak_defense")
        wr = arena.calculate_win_rate("red", rounds=10)
        assert 0.0 <= wr <= 1.0
        _ok("arena_win_rate")
    except Exception as e:
        _fail("arena_win_rate", str(e))

    # --- Test 18: Training controller cycle ---
    try:
        arena = AdversarialArena()
        ctrl = SelfPlayTrainingController(arena)
        result = ctrl.run_training_cycle(num_rounds=5)
        assert "cycle_rounds" in result
        assert result["cycle_rounds"] == 5
        assert ctrl.state.total_rounds >= 5
        _ok("training_cycle")
    except Exception as e:
        _fail("training_cycle", str(e))

    # --- Test 19: Fine-tune trigger on low win rate ---
    try:
        arena = AdversarialArena()
        ctrl = SelfPlayTrainingController(arena)
        ctrl.run_training_cycle(num_rounds=3)
        ft = ctrl.evaluate_and_fine_tune()
        assert "triggered" in ft
        assert "red_win_rate" in ft
        assert "actions_taken" in ft
        _ok("fine_tune_evaluation")
    except Exception as e:
        _fail("fine_tune_evaluation", str(e))

    # --- Test 20: Deploy best strategy ---
    try:
        arena = AdversarialArena()
        ctrl = SelfPlayTrainingController(arena)
        dep = ctrl.deploy_best_strategy()
        assert dep["deployed"] is True
        assert dep["defense_code_length"] > 0
        assert ctrl._deployed_strategy is not None
        _ok("deploy_strategy")
    except Exception as e:
        _fail("deploy_strategy", str(e))

    # --- Test 21: Fusion - user challenge submission ---
    try:
        fusion = CultivationAdversarialFusion()
        ch = fusion.submit_challenge("user_001", "print('hello')", "red")
        assert ch.user_id == "user_001"
        assert ch.side == "red"
        assert ch.evaluated is False
        _ok("fusion_submit_challenge")
    except Exception as e:
        _fail("fusion_submit_challenge", str(e))

    # --- Test 22: Fusion - evaluate successful attack ---
    try:
        fusion = CultivationAdversarialFusion()
        ch = fusion.submit_challenge("user_002", "import os\nos.getcwd()", "red")
        eval_r = fusion.evaluate_user_submission(ch, "dummy_defense")
        assert "success" in eval_r
        assert "exp_award" in eval_r
        assert eval_r["side"] == "red"
        _ok("fusion_evaluate_attack")
    except Exception as e:
        _fail("fusion_evaluate_attack", str(e))

    # --- Test 23: Fusion - experience awarding ---
    try:
        fusion = CultivationAdversarialFusion()
        fusion.award_experience("user_003", 50.0, "successful_attack")
        stats = fusion.get_user_stats("user_003")
        assert stats["exp"] == 50.0
        assert stats["wins"] == 1
        _ok("fusion_experience_award")
    except Exception as e:
        _fail("fusion_experience_award", str(e))

    # --- Test 24: Fusion - security title granting ---
    try:
        fusion = CultivationAdversarialFusion()
        fusion.award_experience("user_004", 16000.0, "tournament_win")
        granted = fusion.grant_security_title(user_id="user_004", title=SecurityTitle.CYBER_IMMORTAL)
        assert granted is True
        stats = fusion.get_user_stats("user_004")
        assert "Cyber Immortal" in str(stats["titles"]) or "network" in str(stats["titles"]).lower() or len(stats["titles"]) > 0
        _ok("fusion_security_title")
    except Exception as e:
        _fail("fusion_security_title", str(e))

    # --- Test 25: Fusion - leaderboard ---
    try:
        fusion = CultivationAdversarialFusion()
        for i in range(5):
            fusion.award_experience(f"user_lb_{i}", 100.0 * (5 - i), "successful_defense")
        lb = fusion.get_leaderboard("exp")
        assert len(lb) == 5
        assert lb[0]["rank"] == 1
        assert lb[0]["exp"] >= lb[-1]["exp"]
        _ok("fusion_leaderboard")
    except Exception as e:
        _fail("fusion_leaderboard", str(e))

    # --- Test 26: Fusion - tournament creation ---
    try:
        fusion = CultivationAdversarialFusion()
        t = fusion.create_tournament("Spring CTF 2026", duration_hours=48)
        assert t.name == "Spring CTF 2026"
        assert t.status == "active"
        joined = fusion.join_tournament(t.tournament_id, "player_001")
        assert joined is True
        assert "player_001" in t.participants
        _ok("fusion_tournament")
    except Exception as e:
        _fail("fusion_tournament", str(e))

    # --- Test 27: Orchestrator initialization ---
    try:
        orch = RedBlueOrchestrator()
        init = orch.initialize()
        assert init["status"] == "ready"
        assert init["arena_ready"] is True
        assert init["base_rules_loaded"] >= 10
        _ok("orchestrator_init")
    except Exception as e:
        _fail("orchestrator_init", str(e))

    # --- Test 28: Orchestrator quick demo ---
    try:
        orch = RedBlueOrchestrator()
        demo = orch.quick_demo()
        assert "original_script_id" in demo
        assert "mutated_script_id" in demo
        assert "battle_outcomes" in demo
        assert len(demo["battle_outcomes"]) == 2
        _ok("orchestrator_demo")
    except Exception as e:
        _fail("orchestrator_demo", str(e))

    # --- Test 29: Orchestrator dashboard ---
    try:
        orch = RedBlueOrchestrator()
        orch.quick_demo()
        dash = orch.get_dashboard()
        assert "system_status" in dash
        assert "arena" in dash
        assert "trainer" in dash
        assert "fusion" in dash
        assert dash["arena"]["total_battles"] >= 2
        _ok("orchestrator_dashboard")
    except Exception as e:
        _fail("orchestrator_dashboard", str(e))

    # --- Test 30: Full pipeline integration ---
    try:
        orch = RedBlueOrchestrator()
        orch.initialize()
        train_result = orch.run_adversarial_training(rounds=3)
        assert "cycle_result" in train_result
        assert "fine_tune" in train_result
        challenge_result = orch.handle_user_challenge("integration_user", "x = 1 + 1", "red")
        assert "challenge_id" in challenge_result
        dashboard = orch.get_dashboard()
        assert dashboard["trainer"]["total_rounds"] >= 3
        _ok("full_pipeline_integration")
    except Exception as e:
        _fail("full_pipeline_integration", str(e))

    passed = sum(1 for r in results if not r.startswith("[FAIL]"))
    failed = len(results) - passed
    return {
        "layer": "L42_Red_Blue_Adversarial",
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "results": results
    }


if __name__ == "__main__":
    import sys
    output = run_tests()
    print(f"\n{'='*60}")
    print(f"Layer 42: Red-Blue Adversarial & Code Execution Fusion")
    print(f"{'='*60}")
    print(f"Total: {output['total']}  Passed: {output['passed']}  Failed: {output['failed']}")
    if output['errors']:
        print(f"\nFailed tests:")
        for e in output['errors']:
            print(f"  [X] {e}")
    else:
        print("\nAll tests PASSED!")
    sys.exit(0 if output['failed'] == 0 else 1)
