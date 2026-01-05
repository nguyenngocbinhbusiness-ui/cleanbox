"""
Functional Suitability Evaluator - ISO/IEC 25010
------------------------------------------------
Measures: Completeness, Correctness, Appropriateness
Tools: pytest, coverage
"""

import subprocess
import json
import sys
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FunctionalResult:
    """Functional suitability evaluation result."""
    test_pass_rate: float  # Percentage of passed tests
    code_coverage: float   # Code coverage percentage
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    total_tests: int
    score: float
    details: Dict[str, Any]


def run_pytest(project_dir: Path) -> Dict[str, Any]:
    """Run pytest and collect results."""
    result = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
        "pass_rate": 0.0,
        "error": None,
    }
    
    try:
        # Run pytest with JSON report
        # Exclude e2e tests to prevent hangs
        test_dirs = ["tests/unit", "tests/ui", "tests/component", "tests/integration"]
        target_args = [str(project_dir / d) for d in test_dirs if (project_dir / d).exists()]
        
        cmd = [
            sys.executable, "-m", "pytest",
            *target_args,
            "-v",
            "--tb=short",
            "-q",
            "--no-header",
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=300,  # 5 minute timeout
        )
        
        # Parse output for test counts
        output = proc.stdout + proc.stderr
        
        # Look for summary line: "X passed, Y failed, Z skipped"
        summary_match = re.search(
            r'(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+(?:skipped|warning))?',
            output
        )
        
        if summary_match:
            result["passed"] = int(summary_match.group(1) or 0)
            result["failed"] = int(summary_match.group(2) or 0)
            result["skipped"] = int(summary_match.group(3) or 0)
        else:
            # Alternative pattern - look for summary line
            passed_match = re.search(r'(\d+)\s+passed', output)
            failed_match = re.search(r'(\d+)\s+failed', output)
            skipped_match = re.search(r'(\d+)\s+skipped', output)
            
            if passed_match or failed_match:
                result["passed"] = int(passed_match.group(1)) if passed_match else 0
                result["failed"] = int(failed_match.group(1)) if failed_match else 0
                result["skipped"] = int(skipped_match.group(1)) if skipped_match else 0
            else:
                # Fallback: count PASSED/FAILED occurrences in verbose output
                # This handles cases where pytest crashes before printing summary
                passed_count = len(re.findall(r'\bPASSED\b', output))
                failed_count = len(re.findall(r'\bFAILED\b', output))
                skipped_count = len(re.findall(r'\bSKIPPED\b', output))
                
                result["passed"] = passed_count
                result["failed"] = failed_count
                result["skipped"] = skipped_count
        
        result["total"] = result["passed"] + result["failed"] + result["skipped"]
        
        if result["total"] > 0:
            # Only count passed vs passed+failed (exclude skipped)
            executable = result["passed"] + result["failed"]
            if executable > 0:
                result["pass_rate"] = (result["passed"] / executable) * 100
            else:
                result["pass_rate"] = 100.0
        
        result["output"] = output[:2000]  # Truncate output
        
    except subprocess.TimeoutExpired:
        result["error"] = "Pytest timed out after 5 minutes"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def run_coverage(project_dir: Path) -> Dict[str, Any]:
    """Run coverage analysis."""
    result = {
        "coverage_percent": 0.0,
        "covered_lines": 0,
        "total_lines": 0,
        "error": None,
    }
    
    try:
        # Run coverage
        # Exclude e2e tests
        test_dirs = ["tests/unit", "tests/ui", "tests/component", "tests/integration"]
        target_args = [str(project_dir / d) for d in test_dirs if (project_dir / d).exists()]

        cmd = [
            sys.executable, "-m", "coverage", "run",
            "--source", str(project_dir / "src"),
            "-m", "pytest",
            *target_args,
            "-q",
            "--no-header",
        ]
        
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=300,
        )
        
        # Get coverage report as JSON
        report_cmd = [
            sys.executable, "-m", "coverage", "json",
            "-o", "-",  # Output to stdout
        ]
        
        report_proc = subprocess.run(
            report_cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=60,
        )
        
        if report_proc.returncode == 0 and report_proc.stdout:
            coverage_data = json.loads(report_proc.stdout)
            totals = coverage_data.get("totals", {})
            result["coverage_percent"] = totals.get("percent_covered", 0.0)
            result["covered_lines"] = totals.get("covered_lines", 0)
            result["total_lines"] = totals.get("num_statements", 0)
        else:
            # Fallback: parse text report
            text_cmd = [sys.executable, "-m", "coverage", "report"]
            text_proc = subprocess.run(
                text_cmd,
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=60,
            )
            
            # Parse TOTAL line
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', text_proc.stdout)
            if match:
                result["coverage_percent"] = float(match.group(1))
        
    except subprocess.TimeoutExpired:
        result["error"] = "Coverage analysis timed out"
    except Exception as e:
        result["error"] = str(e)
    
    # Fallback: Try to load from existing coverage.json file if no coverage collected
    if result["coverage_percent"] == 0.0:
        coverage_json_path = project_dir / "coverage.json"
        if coverage_json_path.exists():
            try:
                with open(coverage_json_path, 'r', encoding='utf-8') as f:
                    coverage_data = json.load(f)
                totals = coverage_data.get("totals", {})
                result["coverage_percent"] = totals.get("percent_covered", 0.0)
                result["covered_lines"] = totals.get("covered_lines", 0)
                result["total_lines"] = totals.get("num_statements", 0)
                result["error"] = None  # Clear error if we got data from file
            except Exception:
                pass  # Keep original error
    
    return result


def evaluate(project_dir: Path) -> FunctionalResult:
    """
    Evaluate functional suitability.
    
    Score calculation:
    - 60% weight: Test pass rate
    - 40% weight: Code coverage
    """
    # Run evaluations
    pytest_result = run_pytest(project_dir)
    coverage_result = run_coverage(project_dir)
    
    # Calculate component scores
    test_pass_rate = pytest_result.get("pass_rate", 0.0)
    code_coverage = coverage_result.get("coverage_percent", 0.0)
    
    # Weighted score
    score = (test_pass_rate * 0.6) + (code_coverage * 0.4)
    
    return FunctionalResult(
        test_pass_rate=test_pass_rate,
        code_coverage=code_coverage,
        tests_passed=pytest_result.get("passed", 0),
        tests_failed=pytest_result.get("failed", 0),
        tests_skipped=pytest_result.get("skipped", 0),
        total_tests=pytest_result.get("total", 0),
        score=score,
        details={
            "pytest": pytest_result,
            "coverage": coverage_result,
        }
    )


if __name__ == "__main__":
    # Test the evaluator
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Functional Suitability Score: {result.score:.1f}%")
    print(f"  Test Pass Rate: {result.test_pass_rate:.1f}%")
    print(f"  Code Coverage: {result.code_coverage:.1f}%")
    print(f"  Tests: {result.tests_passed}/{result.total_tests} passed")
