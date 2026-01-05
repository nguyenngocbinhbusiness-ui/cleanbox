"""
Portability Evaluator - ISO/IEC 25010
-------------------------------------
Measures: Adaptability, Installability, Replaceability
Checks: Hardcoded paths, platform-specific code, dependency portability
"""

import ast
import re
import platform
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class PortabilityResult:
    """Portability evaluation result."""
    hardcoded_paths: int
    platform_specific_imports: int
    has_requirements_file: bool
    has_setup_config: bool
    score: float
    details: Dict[str, Any]


def check_hardcoded_paths(project_dir: Path) -> Dict[str, Any]:
    """Check for hardcoded paths in code."""
    result = {
        "hardcoded_paths": 0,
        "examples": [],
        "error": None,
    }
    
    # Patterns for hardcoded paths
    path_patterns = [
        (r'["\'][A-Za-z]:\\[^"\']+["\']', 'Windows absolute path'),
        (r'["\']/home/[^"\']+["\']', 'Unix home path'),
        (r'["\']/usr/[^"\']+["\']', 'Unix system path'),
        (r'["\']C:\\Users\\[^"\']+["\']', 'Windows user path'),
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
                
                for pattern, description in path_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Ignore common acceptable patterns
                        if not any(ok in match.lower() for ok in ['appdata', 'temp', 'programdata']):
                            result["hardcoded_paths"] += 1
                            if len(result["examples"]) < 5:
                                result["examples"].append({
                                    "file": str(py_file.relative_to(project_dir)),
                                    "path": match[:50],
                                    "type": description,
                                })
                
            except Exception:
                continue
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_platform_specific_code(project_dir: Path) -> Dict[str, Any]:
    """Check for platform-specific imports and code."""
    result = {
        "windows_specific": 0,
        "unix_specific": 0,
        "platform_checks": 0,  # Proper platform checks (good)
        "modules": [],
        "error": None,
    }
    
    windows_modules = ['win32api', 'win32con', 'win32gui', 'winreg', 'msvcrt', 'winshell']
    unix_modules = ['posix', 'pwd', 'grp', 'fcntl']
    
    try:
        src_dir = project_dir / "src"
        if not src_dir.exists():
            src_dir = project_dir
        
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in windows_modules:
                                result["windows_specific"] += 1
                                result["modules"].append(alias.name)
                            elif alias.name in unix_modules:
                                result["unix_specific"] += 1
                                result["modules"].append(alias.name)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module in windows_modules:
                            result["windows_specific"] += 1
                            result["modules"].append(node.module)
                        elif node.module in unix_modules:
                            result["unix_specific"] += 1
                            result["modules"].append(node.module)
                
                # Check for proper platform checks
                content = py_file.read_text(encoding='utf-8')
                result["platform_checks"] += len(re.findall(
                    r'platform\.system\(\)|sys\.platform|os\.name',
                    content
                ))
                
            except (SyntaxError, Exception):
                continue
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_installation_support(project_dir: Path) -> Dict[str, Any]:
    """Check for installation and packaging support."""
    result = {
        "has_requirements": False,
        "has_setup_py": False,
        "has_setup_cfg": False,
        "has_pyproject": False,
        "has_dockerfile": False,
        "has_readme": False,
        "error": None,
    }
    
    try:
        result["has_requirements"] = (project_dir / "requirements.txt").exists()
        result["has_setup_py"] = (project_dir / "setup.py").exists()
        result["has_setup_cfg"] = (project_dir / "setup.cfg").exists()
        result["has_pyproject"] = (project_dir / "pyproject.toml").exists()
        result["has_dockerfile"] = (project_dir / "Dockerfile").exists()
        result["has_readme"] = (project_dir / "README.md").exists()
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> PortabilityResult:
    """
    Evaluate portability.
    
    Score calculation:
    - No hardcoded paths: 30 points (deduct 5 per hardcoded path, min 0)
    - Platform handling: 30 points
    - Installation support: 40 points
    """
    # Run checks
    paths_result = check_hardcoded_paths(project_dir)
    platform_result = check_platform_specific_code(project_dir)
    install_result = check_installation_support(project_dir)
    
    # Calculate path score
    hardcoded_paths = paths_result.get("hardcoded_paths", 0)
    path_score = max(0, 30 - (hardcoded_paths * 5))
    
    # Platform score
    # For a Windows-only app, having Windows-specific code is expected
    # Give full points if platform checks exist or if it's platform-specific by design
    platform_checks = platform_result.get("platform_checks", 0)
    windows_specific = platform_result.get("windows_specific", 0)
    
    if platform_checks > 0 or windows_specific == 0:
        platform_score = 30
    elif windows_specific <= 5:
        platform_score = 20
    else:
        platform_score = 10
    
    # Installation score
    install_score = 0
    if install_result.get("has_requirements", False):
        install_score += 15
    if install_result.get("has_readme", False):
        install_score += 10
    if install_result.get("has_pyproject", False) or install_result.get("has_setup_py", False):
        install_score += 10
    if install_result.get("has_dockerfile", False):
        install_score += 5
    
    total_score = path_score + platform_score + install_score
    
    return PortabilityResult(
        hardcoded_paths=hardcoded_paths,
        platform_specific_imports=windows_specific + platform_result.get("unix_specific", 0),
        has_requirements_file=install_result.get("has_requirements", False),
        has_setup_config=install_result.get("has_pyproject", False) or install_result.get("has_setup_py", False),
        score=min(100.0, total_score),
        details={
            "paths": paths_result,
            "platform": platform_result,
            "installation": install_result,
            "component_scores": {
                "paths": path_score,
                "platform": platform_score,
                "installation": install_score,
            }
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Portability Score: {result.score:.1f}%")
    print(f"  Hardcoded paths: {result.hardcoded_paths}")
    print(f"  Platform-specific imports: {result.platform_specific_imports}")
    print(f"  Has requirements.txt: {result.has_requirements_file}")
