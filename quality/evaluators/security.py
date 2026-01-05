"""
Security Evaluator - ISO/IEC 25010
----------------------------------
Measures: Confidentiality, Integrity, Non-repudiation, Accountability, Authenticity
Tools: bandit (static analysis), pip-audit (dependency vulnerabilities)
"""

import subprocess
import sys
import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class SecurityResult:
    """Security evaluation result."""
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_medium: int
    vulnerabilities_low: int
    dependency_vulnerabilities: int
    hardcoded_secrets: int
    score: float
    details: Dict[str, Any]


def run_bandit(project_dir: Path) -> Dict[str, Any]:
    """Run bandit security scanner."""
    result = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "total_issues": 0,
        "issues": [],
        "error": None,
    }
    
    try:
        cmd = [
            sys.executable, "-m", "bandit",
            "-r", str(project_dir / "src"),
            "-f", "json",
            "-q",
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
                results = data.get("results", [])
                
                for issue in results:
                    severity = issue.get("issue_severity", "").upper()
                    if severity == "HIGH":
                        result["high"] += 1
                    elif severity == "MEDIUM":
                        result["medium"] += 1
                    elif severity == "LOW":
                        result["low"] += 1
                    
                    result["issues"].append({
                        "severity": severity,
                        "text": issue.get("issue_text", ""),
                        "file": issue.get("filename", ""),
                        "line": issue.get("line_number", 0),
                    })
                
                result["total_issues"] = len(results)
                
            except json.JSONDecodeError:
                result["error"] = "Failed to parse bandit output"
        
    except FileNotFoundError:
        result["error"] = "bandit not installed (pip install bandit)"
    except subprocess.TimeoutExpired:
        result["error"] = "Bandit scan timed out"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def run_pip_audit(project_dir: Path) -> Dict[str, Any]:
    """Run pip-audit for dependency vulnerabilities."""
    result = {
        "vulnerabilities": 0,
        "packages_scanned": 0,
        "issues": [],
        "error": None,
    }
    
    try:
        cmd = [
            sys.executable, "-m", "pip_audit",
            "--format", "json",
        ]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=120,
        )
        
        # pip-audit returns non-zero if vulnerabilities found
        output = proc.stdout if proc.stdout else proc.stderr
        
        if output:
            try:
                data = json.loads(output)
                if isinstance(data, list):
                    result["vulnerabilities"] = len(data)
                    for vuln in data[:10]:  # Limit to first 10
                        result["issues"].append({
                            "package": vuln.get("name", ""),
                            "version": vuln.get("version", ""),
                            "id": vuln.get("id", ""),
                        })
            except json.JSONDecodeError:
                # Try to parse text output
                if "No known vulnerabilities found" in output:
                    result["vulnerabilities"] = 0
                else:
                    result["error"] = "Failed to parse pip-audit output"
        
    except FileNotFoundError:
        result["error"] = "pip-audit not installed (pip install pip-audit)"
    except subprocess.TimeoutExpired:
        result["error"] = "pip-audit timed out"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_hardcoded_secrets(project_dir: Path) -> Dict[str, Any]:
    """Check for potential hardcoded secrets."""
    result = {
        "secrets_found": 0,
        "patterns_matched": [],
        "error": None,
    }
    
    # Patterns that might indicate secrets
    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
        (r'token\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded token'),
        (r'["\'][A-Za-z0-9+/]{40,}["\']', 'Potential base64 secret'),
    ]
    
    try:
        src_dir = project_dir / "src"
        if not src_dir.exists():
            src_dir = project_dir
        
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                for pattern, description in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Filter out common false positives
                        for match in matches:
                            if not any(fp in match.lower() for fp in ['example', 'placeholder', 'your_', 'xxx', 'test']):
                                result["secrets_found"] += 1
                                if description not in result["patterns_matched"]:
                                    result["patterns_matched"].append(description)
                
            except Exception:
                continue
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> SecurityResult:
    """
    Evaluate security.
    
    Score calculation:
    - Start at 100
    - Deduct per issue: Critical=-20, High=-10, Medium=-5, Low=-2
    - Deduct per dependency vulnerability: -5
    - Deduct per hardcoded secret: -10
    - Minimum score: 0
    """
    # Run analyses
    bandit_result = run_bandit(project_dir)
    pip_audit_result = run_pip_audit(project_dir)
    secrets_result = check_hardcoded_secrets(project_dir)
    
    # Calculate score (start at 100, deduct for issues)
    score = 100.0
    
    # Bandit deductions
    score -= bandit_result.get("critical", 0) * 20
    score -= bandit_result.get("high", 0) * 10
    score -= bandit_result.get("medium", 0) * 5
    score -= bandit_result.get("low", 0) * 2
    
    # Dependency vulnerabilities
    score -= pip_audit_result.get("vulnerabilities", 0) * 5
    
    # Hardcoded secrets
    score -= secrets_result.get("secrets_found", 0) * 10
    
    # Ensure minimum 0
    score = max(0.0, score)
    
    return SecurityResult(
        vulnerabilities_critical=bandit_result.get("critical", 0),
        vulnerabilities_high=bandit_result.get("high", 0),
        vulnerabilities_medium=bandit_result.get("medium", 0),
        vulnerabilities_low=bandit_result.get("low", 0),
        dependency_vulnerabilities=pip_audit_result.get("vulnerabilities", 0),
        hardcoded_secrets=secrets_result.get("secrets_found", 0),
        score=score,
        details={
            "bandit": bandit_result,
            "pip_audit": pip_audit_result,
            "secrets": secrets_result,
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Security Score: {result.score:.1f}%")
    print(f"  Critical: {result.vulnerabilities_critical}")
    print(f"  High: {result.vulnerabilities_high}")
    print(f"  Medium: {result.vulnerabilities_medium}")
    print(f"  Low: {result.vulnerabilities_low}")
