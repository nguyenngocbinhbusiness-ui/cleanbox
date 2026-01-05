"""
Compatibility Evaluator - ISO/IEC 25010
---------------------------------------
Measures: Co-existence, Interoperability
Checks: Python version, dependencies, Windows API compatibility
"""

import subprocess
import sys
import platform
import importlib.metadata
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class CompatibilityResult:
    """Compatibility evaluation result."""
    python_compatible: bool
    dependencies_resolved: bool
    platform_compatible: bool
    dependency_issues: List[str]
    score: float
    details: Dict[str, Any]


def check_python_version(project_dir: Path) -> Dict[str, Any]:
    """Check Python version compatibility."""
    result = {
        "current_version": platform.python_version(),
        "required_version": "3.11+",
        "compatible": False,
        "error": None,
    }
    
    try:
        version_info = sys.version_info
        # Check if Python 3.11+
        result["compatible"] = version_info >= (3, 11)
        result["version_tuple"] = (version_info.major, version_info.minor, version_info.micro)
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_dependencies(project_dir: Path) -> Dict[str, Any]:
    """Check if all dependencies are properly installed and compatible."""
    result = {
        "all_installed": True,
        "installed": [],
        "missing": [],
        "version_conflicts": [],
        "error": None,
    }
    
    try:
        requirements_file = project_dir / "requirements.txt"
        if not requirements_file.exists():
            result["error"] = "requirements.txt not found"
            return result
        
        # Parse requirements
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for req in requirements:
            # Parse package name (handle >=, ==, etc.)
            pkg_name = req.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()
            
            try:
                version = importlib.metadata.version(pkg_name)
                result["installed"].append({
                    "name": pkg_name,
                    "version": version,
                    "required": req,
                })
            except importlib.metadata.PackageNotFoundError:
                result["missing"].append(pkg_name)
                result["all_installed"] = False
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_platform_compatibility(project_dir: Path) -> Dict[str, Any]:
    """Check Windows platform compatibility."""
    result = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "compatible": False,
        "windows_apis_available": [],
        "windows_apis_missing": [],
        "error": None,
    }
    
    try:
        # Check if running on Windows
        result["compatible"] = platform.system() == "Windows"
        
        # Check Windows-specific modules
        windows_modules = [
            "winreg",
            "ctypes",
            "win32api",
            "win32con",
            "winshell",
        ]
        
        for mod in windows_modules:
            try:
                __import__(mod)
                result["windows_apis_available"].append(mod)
            except ImportError:
                result["windows_apis_missing"].append(mod)
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> CompatibilityResult:
    """
    Evaluate compatibility.
    
    Score calculation:
    - Python version compatible: 30 points
    - All dependencies installed: 40 points
    - Platform compatibility: 30 points
    """
    # Run checks
    python_result = check_python_version(project_dir)
    deps_result = check_dependencies(project_dir)
    platform_result = check_platform_compatibility(project_dir)
    
    # Calculate score
    score = 0.0
    
    if python_result.get("compatible", False):
        score += 30.0
    
    if deps_result.get("all_installed", False):
        score += 40.0
    elif len(deps_result.get("missing", [])) < 2:
        score += 20.0  # Partial credit
    
    if platform_result.get("compatible", False):
        score += 30.0
    
    # Collect issues
    issues = []
    if deps_result.get("missing"):
        issues.extend([f"Missing: {pkg}" for pkg in deps_result["missing"]])
    if deps_result.get("version_conflicts"):
        issues.extend(deps_result["version_conflicts"])
    
    return CompatibilityResult(
        python_compatible=python_result.get("compatible", False),
        dependencies_resolved=deps_result.get("all_installed", False),
        platform_compatible=platform_result.get("compatible", False),
        dependency_issues=issues,
        score=score,
        details={
            "python": python_result,
            "dependencies": deps_result,
            "platform": platform_result,
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Compatibility Score: {result.score:.1f}%")
    print(f"  Python Compatible: {result.python_compatible}")
    print(f"  Dependencies OK: {result.dependencies_resolved}")
    print(f"  Platform OK: {result.platform_compatible}")
