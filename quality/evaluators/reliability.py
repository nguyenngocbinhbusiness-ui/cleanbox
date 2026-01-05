"""
Reliability Evaluator - ISO/IEC 25010
-------------------------------------
Measures: Maturity, Availability, Fault Tolerance, Recoverability
Checks: Exception handling, error patterns, resource cleanup
"""

import ast
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ReliabilityResult:
    """Reliability evaluation result."""
    exception_handling_ratio: float
    resource_cleanup_ratio: float
    error_logging_present: bool
    patterns_found: List[str]
    score: float
    details: Dict[str, Any]


class ReliabilityAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze reliability patterns."""
    
    def __init__(self):
        self.functions_total = 0
        self.functions_with_try = 0
        self.functions_with_finally = 0
        self.context_managers_used = 0
        self.bare_excepts = 0
        self.logging_calls = 0
        self.resource_opens = 0
        self.resource_closes = 0
    
    def visit_FunctionDef(self, node):
        self.functions_total += 1
        
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                self.functions_with_try += 1
                if child.finalbody:
                    self.functions_with_finally += 1
                
                # Check for bare excepts
                for handler in child.handlers:
                    if handler.type is None:
                        self.bare_excepts += 1
                break
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
    
    def visit_With(self, node):
        self.context_managers_used += 1
        self.generic_visit(node)
    
    def visit_AsyncWith(self, node):
        self.context_managers_used += 1
        self.generic_visit(node)
    
    def visit_Call(self, node):
        # Check for logging calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ('debug', 'info', 'warning', 'error', 'critical', 'exception'):
                self.logging_calls += 1
            elif node.func.attr == 'open':
                self.resource_opens += 1
            elif node.func.attr == 'close':
                self.resource_closes += 1
        elif isinstance(node.func, ast.Name):
            if node.func.id == 'open':
                self.resource_opens += 1
        
        self.generic_visit(node)


def analyze_reliability_patterns(project_dir: Path) -> Dict[str, Any]:
    """Analyze reliability patterns in code."""
    result = {
        "functions_total": 0,
        "functions_with_try": 0,
        "exception_handling_ratio": 0.0,
        "context_managers_used": 0,
        "bare_excepts": 0,
        "logging_calls": 0,
        "patterns_found": [],
        "error": None,
    }
    
    try:
        src_dir = project_dir / "src"
        if not src_dir.exists():
            src_dir = project_dir
        
        analyzer = ReliabilityAnalyzer()
        
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                analyzer.visit(tree)
            except SyntaxError:
                continue
        
        result["functions_total"] = analyzer.functions_total
        result["functions_with_try"] = analyzer.functions_with_try
        result["functions_with_finally"] = analyzer.functions_with_finally
        result["context_managers_used"] = analyzer.context_managers_used
        result["bare_excepts"] = analyzer.bare_excepts
        result["logging_calls"] = analyzer.logging_calls
        
        if analyzer.functions_total > 0:
            result["exception_handling_ratio"] = (
                analyzer.functions_with_try / analyzer.functions_total * 100
            )
            result["resource_cleanup_ratio"] = (
                (analyzer.functions_with_finally + analyzer.context_managers_used) 
                / analyzer.functions_total * 100
            )
        
        # Identify good patterns
        if analyzer.context_managers_used > 0:
            result["patterns_found"].append("Context managers used for resource management")
        if analyzer.logging_calls > 0:
            result["patterns_found"].append("Logging is implemented")
        if analyzer.bare_excepts == 0:
            result["patterns_found"].append("No bare except clauses (good practice)")
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_recovery_mechanisms(project_dir: Path) -> Dict[str, Any]:
    """Check for recovery and fallback mechanisms."""
    result = {
        "config_backup": False,
        "graceful_shutdown": False,
        "retry_patterns": 0,
        "error": None,
    }
    
    try:
        src_dir = project_dir / "src"
        if not src_dir.exists():
            src_dir = project_dir
        
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for backup/recovery patterns
                if re.search(r'backup|recover|restore', content, re.IGNORECASE):
                    result["config_backup"] = True
                
                # Check for graceful shutdown
                if re.search(r'signal|atexit|cleanup|shutdown', content, re.IGNORECASE):
                    result["graceful_shutdown"] = True
                
                # Check for retry patterns
                result["retry_patterns"] += len(re.findall(r'retry|attempt|max_retries', content, re.IGNORECASE))
                
            except Exception:
                continue
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> ReliabilityResult:
    """
    Evaluate reliability.
    
    Score calculation:
    - Exception handling ratio: up to 40 points
    - No bare excepts: 15 points
    - Context managers used: 15 points
    - Logging present: 15 points
    - Recovery mechanisms: 15 points
    """
    # Run analyses
    patterns_result = analyze_reliability_patterns(project_dir)
    recovery_result = check_recovery_mechanisms(project_dir)
    
    # Calculate score
    score = 0.0
    
    # Exception handling score (max 40)
    exception_ratio = patterns_result.get("exception_handling_ratio", 0)
    score += min(40.0, exception_ratio * 0.4)
    
    # No bare excepts bonus
    if patterns_result.get("bare_excepts", 1) == 0:
        score += 15.0
    elif patterns_result.get("bare_excepts", 0) < 3:
        score += 7.5
    
    # Context managers
    if patterns_result.get("context_managers_used", 0) > 0:
        score += 15.0
    
    # Logging
    if patterns_result.get("logging_calls", 0) > 0:
        score += 15.0
    
    # Recovery mechanisms
    recovery_score = 0
    if recovery_result.get("config_backup", False):
        recovery_score += 5
    if recovery_result.get("graceful_shutdown", False):
        recovery_score += 5
    if recovery_result.get("retry_patterns", 0) > 0:
        recovery_score += 5
    score += recovery_score
    
    # Calculate resource cleanup ratio
    resource_cleanup_ratio = patterns_result.get("resource_cleanup_ratio", 0)
    
    # Add bonus for finally blocks / context managers
    if resource_cleanup_ratio > 0:
        score += min(10.0, resource_cleanup_ratio * 0.5)
    
    patterns_found = patterns_result.get("patterns_found", [])
    if patterns_result.get("functions_with_finally", 0) > 0:
        patterns_found.append("Finally blocks used for cleanup")
    
    return ReliabilityResult(
        exception_handling_ratio=exception_ratio,
        resource_cleanup_ratio=resource_cleanup_ratio,
        error_logging_present=patterns_result.get("logging_calls", 0) > 0,
        patterns_found=patterns_found,
        score=min(100.0, score),
        details={
            "patterns": patterns_result,
            "recovery": recovery_result,
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Reliability Score: {result.score:.1f}%")
    print(f"  Exception handling: {result.exception_handling_ratio:.1f}%")
    print(f"  Logging present: {result.error_logging_present}")
    print(f"  Patterns: {', '.join(result.patterns_found)}")
