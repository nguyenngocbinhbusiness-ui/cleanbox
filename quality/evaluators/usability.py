"""
Usability Evaluator - ISO/IEC 25010
-----------------------------------
Measures: Recognizability, Learnability, Operability, Error Protection
Checks: Documentation, error messages, docstrings
"""

import ast
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class UsabilityResult:
    """Usability evaluation result."""
    docstring_coverage: float     # Percentage of functions with docstrings
    readme_exists: bool
    error_handling_coverage: float  # Percentage of functions with try/except
    score: float
    details: Dict[str, Any]


class DocstringAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze docstrings."""
    
    def __init__(self):
        self.functions_total = 0
        self.functions_with_docs = 0
        self.classes_total = 0
        self.classes_with_docs = 0
        self.functions_with_error_handling = 0
    
    def visit_FunctionDef(self, node):
        self.functions_total += 1
        if ast.get_docstring(node):
            self.functions_with_docs += 1
        
        # Check for error handling
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                self.functions_with_error_handling += 1
                break
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node):
        self.classes_total += 1
        if ast.get_docstring(node):
            self.classes_with_docs += 1
        self.generic_visit(node)


def analyze_documentation(project_dir: Path) -> Dict[str, Any]:
    """Analyze documentation coverage."""
    result = {
        "readme_exists": False,
        "readme_lines": 0,
        "docs_dir_exists": False,
        "doc_files_count": 0,
        "error": None,
    }
    
    try:
        # Check README
        readme_path = project_dir / "README.md"
        if readme_path.exists():
            result["readme_exists"] = True
            result["readme_lines"] = len(readme_path.read_text().splitlines())
        
        # Check docs directory
        docs_dir = project_dir / "docs"
        if docs_dir.exists() and docs_dir.is_dir():
            result["docs_dir_exists"] = True
            result["doc_files_count"] = len(list(docs_dir.glob("*.md")))
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def analyze_code_documentation(project_dir: Path) -> Dict[str, Any]:
    """Analyze docstring coverage in Python files."""
    result = {
        "functions_total": 0,
        "functions_documented": 0,
        "docstring_coverage": 0.0,
        "classes_total": 0,
        "classes_documented": 0,
        "functions_with_error_handling": 0,
        "error_handling_coverage": 0.0,
        "error": None,
    }
    
    try:
        src_dir = project_dir / "src"
        if not src_dir.exists():
            src_dir = project_dir
        
        analyzer = DocstringAnalyzer()
        
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
        result["functions_documented"] = analyzer.functions_with_docs
        result["classes_total"] = analyzer.classes_total
        result["classes_documented"] = analyzer.classes_with_docs
        result["functions_with_error_handling"] = analyzer.functions_with_error_handling
        
        if analyzer.functions_total > 0:
            result["docstring_coverage"] = (
                analyzer.functions_with_docs / analyzer.functions_total * 100
            )
            result["error_handling_coverage"] = (
                analyzer.functions_with_error_handling / analyzer.functions_total * 100
            )
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> UsabilityResult:
    """
    Evaluate usability.
    
    Score calculation:
    - README exists: 20 points
    - Docstring coverage: up to 50 points (scaled by percentage)
    - Error handling coverage: up to 30 points (scaled by percentage)
    """
    # Run analyses
    doc_result = analyze_documentation(project_dir)
    code_doc_result = analyze_code_documentation(project_dir)
    
    # Calculate score
    score = 0.0
    
    # README score
    if doc_result.get("readme_exists", False):
        score += 20.0
        if doc_result.get("readme_lines", 0) > 50:
            score += 5.0  # Bonus for comprehensive README
    
    # Docstring coverage score (max 50)
    docstring_coverage = code_doc_result.get("docstring_coverage", 0)
    score += min(50.0, docstring_coverage * 0.5)
    
    # Error handling score (max 25)
    error_handling = code_doc_result.get("error_handling_coverage", 0)
    score += min(25.0, error_handling * 0.25)
    
    return UsabilityResult(
        docstring_coverage=docstring_coverage,
        readme_exists=doc_result.get("readme_exists", False),
        error_handling_coverage=error_handling,
        score=min(100.0, score),  # Cap at 100
        details={
            "documentation": doc_result,
            "code_documentation": code_doc_result,
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Usability Score: {result.score:.1f}%")
    print(f"  README exists: {result.readme_exists}")
    print(f"  Docstring coverage: {result.docstring_coverage:.1f}%")
    print(f"  Error handling: {result.error_handling_coverage:.1f}%")
