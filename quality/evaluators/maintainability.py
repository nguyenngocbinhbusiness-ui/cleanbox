"""
Maintainability Evaluator - ISO/IEC 25010
-----------------------------------------
Measures: Modularity, Reusability, Analysability, Modifiability, Testability
Tools: radon (complexity), pylint/flake8 (code quality)
"""

import subprocess
import sys
import json
import ast
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class MaintainabilityResult:
    """Maintainability evaluation result."""
    avg_cyclomatic_complexity: float
    maintainability_index: float
    code_duplication_percent: float
    lint_score: float
    loc: int
    score: float
    details: Dict[str, Any]


def run_radon_cc(project_dir: Path) -> Dict[str, Any]:
    """Run radon cyclomatic complexity analysis."""
    result = {
        "average_complexity": 0.0,
        "max_complexity": 0,
        "functions_analyzed": 0,
        "high_complexity_functions": [],
        "error": None,
    }
    
    try:
        cmd = [
            sys.executable, "-m", "radon", "cc",
            str(project_dir / "src"),
            "-a", "-j",  # Average and JSON output
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=120,
        )
        
        if proc.stdout:
            try:
                data = json.loads(proc.stdout)
                
                total_complexity = 0
                count = 0
                
                for file_path, functions in data.items():
                    if isinstance(functions, list):
                        for func in functions:
                            complexity = func.get("complexity", 0)
                            total_complexity += complexity
                            count += 1
                            
                            if complexity > result["max_complexity"]:
                                result["max_complexity"] = complexity
                            
                            if complexity > 10:  # High complexity threshold
                                result["high_complexity_functions"].append({
                                    "name": func.get("name", ""),
                                    "complexity": complexity,
                                    "file": file_path,
                                })
                
                result["functions_analyzed"] = count
                if count > 0:
                    result["average_complexity"] = total_complexity / count
                
            except json.JSONDecodeError:
                # Parse text output for average
                match = re.search(r'Average complexity: (\w) \(([\d.]+)\)', proc.stdout)
                if match:
                    result["average_complexity"] = float(match.group(2))
        
    except FileNotFoundError:
        result["error"] = "radon not installed (pip install radon)"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def run_radon_mi(project_dir: Path) -> Dict[str, Any]:
    """Run radon maintainability index analysis."""
    result = {
        "average_mi": 0.0,
        "files_analyzed": 0,
        "grades": {"A": 0, "B": 0, "C": 0, "F": 0},
        "error": None,
    }
    
    try:
        cmd = [
            sys.executable, "-m", "radon", "mi",
            str(project_dir / "src"),
            "-j",  # JSON output
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=120,
        )
        
        if proc.stdout:
            try:
                data = json.loads(proc.stdout)
                
                total_mi = 0
                count = 0
                
                for file_path, mi_data in data.items():
                    if isinstance(mi_data, dict):
                        mi = mi_data.get("mi", 0)
                        rank = mi_data.get("rank", "F")
                        
                        total_mi += mi
                        count += 1
                        
                        if rank in result["grades"]:
                            result["grades"][rank] += 1
                
                result["files_analyzed"] = count
                if count > 0:
                    result["average_mi"] = total_mi / count
                
            except json.JSONDecodeError:
                result["error"] = "Failed to parse radon MI output"
        
    except FileNotFoundError:
        result["error"] = "radon not installed"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def analyze_code_metrics(project_dir: Path) -> Dict[str, Any]:
    """Analyze basic code metrics."""
    result = {
        "total_loc": 0,
        "total_files": 0,
        "avg_file_size": 0,
        "large_files": [],  # Files > 500 lines
        "error": None,
    }
    
    try:
        src_dir = project_dir / "src"
        if not src_dir.exists():
            src_dir = project_dir
        
        total_lines = 0
        file_count = 0
        
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                lines = len(py_file.read_text(encoding='utf-8').splitlines())
                total_lines += lines
                file_count += 1
                
                if lines > 500:
                    result["large_files"].append({
                        "file": str(py_file.relative_to(project_dir)),
                        "lines": lines,
                    })
                
            except Exception:
                continue
        
        result["total_loc"] = total_lines
        result["total_files"] = file_count
        if file_count > 0:
            result["avg_file_size"] = total_lines / file_count
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def run_flake8(project_dir: Path) -> Dict[str, Any]:
    """Run flake8 for code style checking."""
    result = {
        "issues": 0,
        "score": 100.0,
        "error": None,
    }
    
    try:
        cmd = [
            sys.executable, "-m", "flake8",
            str(project_dir / "src"),
            "--count",
            "--statistics",
            "--max-line-length", "120",
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=60,
        )
        
        # Count issues from output lines
        output_lines = proc.stdout.strip().split('\n')
        result["issues"] = len([l for l in output_lines if l and ':' in l])
        
        # Calculate score (deduct 1 point per issue, min 0)
        result["score"] = max(0, 100 - result["issues"])
        
    except FileNotFoundError:
        result["error"] = "flake8 not installed (pip install flake8)"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> MaintainabilityResult:
    """
    Evaluate maintainability.
    
    Score calculation:
    - Cyclomatic complexity: 30 points (CC < 5 = 30, < 10 = 20, < 15 = 10, >= 15 = 0)
    - Maintainability index: 40 points (scaled from 0-100 MI)
    - Lint score: 30 points (scaled from flake8 results)
    """
    # Run analyses
    cc_result = run_radon_cc(project_dir)
    mi_result = run_radon_mi(project_dir)
    metrics_result = analyze_code_metrics(project_dir)
    flake8_result = run_flake8(project_dir)
    
    # Calculate complexity score
    avg_cc = cc_result.get("average_complexity", 10)
    if avg_cc < 5:
        cc_score = 30
    elif avg_cc < 10:
        cc_score = 20
    elif avg_cc < 15:
        cc_score = 10
    else:
        cc_score = 0
    
    # Maintainability index score (MI is 0-100, we want 0-40)
    avg_mi = mi_result.get("average_mi", 50)
    mi_score = (avg_mi / 100) * 40
    
    # Lint score (already 0-100, we want 0-30)
    lint_score = (flake8_result.get("score", 50) / 100) * 30
    
    total_score = cc_score + mi_score + lint_score
    
    return MaintainabilityResult(
        avg_cyclomatic_complexity=avg_cc,
        maintainability_index=avg_mi,
        code_duplication_percent=0,  # Would need additional tool
        lint_score=flake8_result.get("score", 0),
        loc=metrics_result.get("total_loc", 0),
        score=min(100.0, total_score),
        details={
            "cyclomatic_complexity": cc_result,
            "maintainability_index": mi_result,
            "metrics": metrics_result,
            "flake8": flake8_result,
            "component_scores": {
                "complexity": cc_score,
                "mi": mi_score,
                "lint": lint_score,
            }
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Maintainability Score: {result.score:.1f}%")
    print(f"  Avg Cyclomatic Complexity: {result.avg_cyclomatic_complexity:.1f}")
    print(f"  Maintainability Index: {result.maintainability_index:.1f}")
    print(f"  Lines of Code: {result.loc}")
