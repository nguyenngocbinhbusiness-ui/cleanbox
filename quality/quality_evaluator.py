"""
ISO/IEC 25010 Quality Evaluator
-------------------------------
Main orchestrator for running all quality evaluations and generating reports.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python < 3.7 or not supported

from quality.config import get_status, get_overall_status, WEIGHTS
from quality.evaluators import functional_suitability
from quality.evaluators import performance_efficiency
from quality.evaluators import compatibility
from quality.evaluators import usability
from quality.evaluators import reliability
from quality.evaluators import security
from quality.evaluators import maintainability
from quality.evaluators import portability


class QualityEvaluator:
    """Main quality evaluator orchestrator."""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.results = {}
        self.overall_score = 0.0
    
    def run_all(self) -> Dict[str, Any]:
        """Run all quality evaluations."""
        print("=" * 60)
        print("ISO/IEC 25010 Quality Evaluation")
        print("=" * 60)
        print(f"Project: {self.project_dir}")
        print(f"Started: {datetime.now().isoformat()}")
        print("-" * 60)
        
        evaluators = [
            ("functional_suitability", functional_suitability.evaluate, "Functional Suitability"),
            ("performance_efficiency", performance_efficiency.evaluate, "Performance Efficiency"),
            ("compatibility", compatibility.evaluate, "Compatibility"),
            ("usability", usability.evaluate, "Usability"),
            ("reliability", reliability.evaluate, "Reliability"),
            ("security", security.evaluate, "Security"),
            ("maintainability", maintainability.evaluate, "Maintainability"),
            ("portability", portability.evaluate, "Portability"),
        ]
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for key, evaluator_func, display_name in evaluators:
            print(f"\n[{display_name}]")
            try:
                result = evaluator_func(self.project_dir)
                score = result.score
                status = get_status(key, score)
                
                self.results[key] = {
                    "score": score,
                    "status": status,
                    "result": self._serialize_result(result),
                }
                
                weight = WEIGHTS.get(key, 1.0)
                total_weighted_score += score * weight
                total_weight += weight
                
                status_icon = {"PASS": "✓", "WARNING": "!", "FAIL": "✗"}.get(status, "?")
                print(f"  Score: {score:.1f}% [{status_icon} {status}]")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                self.results[key] = {
                    "score": 0.0,
                    "status": "ERROR",
                    "error": str(e),
                }
        
        # Calculate overall score
        if total_weight > 0:
            self.overall_score = total_weighted_score / total_weight
        
        print("\n" + "=" * 60)
        overall_status = get_overall_status(self.overall_score)
        status_icon = {"PASS": "✓", "WARNING": "!", "FAIL": "✗"}.get(overall_status, "?")
        print(f"OVERALL SCORE: {self.overall_score:.1f}% [{status_icon} {overall_status}]")
        print("=" * 60)
        
        return self.get_report()
    
    def _serialize_result(self, result) -> Dict[str, Any]:
        """Serialize a result object to dict."""
        if hasattr(result, '__dataclass_fields__'):
            data = asdict(result)
            # Remove nested details to keep report clean
            if 'details' in data:
                del data['details']
            return data
        return {}
    
    def get_report(self) -> Dict[str, Any]:
        """Get the full quality report."""
        return {
            "project": str(self.project_dir),
            "timestamp": datetime.now().isoformat(),
            "overall_score": self.overall_score,
            "overall_status": get_overall_status(self.overall_score),
            "characteristics": self.results,
        }
    
    def save_json_report(self, output_path: Path) -> None:
        """Save report as JSON."""
        report = self.get_report()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nJSON report saved: {output_path}")
    
    def save_markdown_report(self, output_path: Path) -> None:
        """Save report as Markdown."""
        report = self.get_report()
        
        md_lines = [
            "# ISO/IEC 25010 Quality Report",
            "",
            f"**Project:** `{report['project']}`",
            f"**Generated:** {report['timestamp']}",
            "",
            "---",
            "",
            "## Overall Score",
            "",
            f"### {report['overall_score']:.1f}% - {report['overall_status']}",
            "",
        ]
        
        # Add score bar
        score = int(report['overall_score'])
        bar = "█" * (score // 5) + "░" * ((100 - score) // 5)
        md_lines.append(f"```")
        md_lines.append(f"[{bar}] {score}%")
        md_lines.append(f"```")
        md_lines.append("")
        
        # Summary table
        md_lines.extend([
            "## Summary",
            "",
            "| Characteristic | Score | Status |",
            "|----------------|-------|--------|",
        ])
        
        for key, data in report['characteristics'].items():
            display_name = key.replace('_', ' ').title()
            score = data.get('score', 0)
            status = data.get('status', 'UNKNOWN')
            
            emoji = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌", "ERROR": "🔴"}.get(status, "❓")
            md_lines.append(f"| {display_name} | {score:.1f}% | {emoji} {status} |")
        
        md_lines.append("")
        
        # Detailed sections
        md_lines.extend([
            "---",
            "",
            "## Detailed Results",
            "",
        ])
        
        for key, data in report['characteristics'].items():
            display_name = key.replace('_', ' ').title()
            score = data.get('score', 0)
            status = data.get('status', 'UNKNOWN')
            
            md_lines.append(f"### {display_name}")
            md_lines.append("")
            md_lines.append(f"**Score:** {score:.1f}% | **Status:** {status}")
            md_lines.append("")
            
            # Add result details
            result = data.get('result', {})
            if result:
                for k, v in result.items():
                    if k != 'score' and v is not None:
                        md_lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
            
            md_lines.append("")
        
        # Recommendations
        md_lines.extend([
            "---",
            "",
            "## Recommendations",
            "",
        ])
        
        for key, data in report['characteristics'].items():
            if data.get('status') in ('WARNING', 'FAIL'):
                display_name = key.replace('_', ' ').title()
                md_lines.append(f"- **{display_name}** needs improvement (current: {data.get('score', 0):.1f}%)")
        
        if all(d.get('status') == 'PASS' for d in report['characteristics'].values()):
            md_lines.append("✅ All quality characteristics meet the thresholds!")
        
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*Generated by ISO/IEC 25010 Quality Evaluator*")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        print(f"Markdown report saved: {output_path}")


def run_quality_evaluation(project_dir: Path = None) -> Dict[str, Any]:
    """Run quality evaluation and return results."""
    if project_dir is None:
        project_dir = Path(__file__).parent.parent
    
    evaluator = QualityEvaluator(project_dir)
    report = evaluator.run_all()
    
    # Save reports
    reports_dir = project_dir / "quality" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    evaluator.save_json_report(reports_dir / "quality_report.json")
    evaluator.save_markdown_report(reports_dir / "quality_report.md")
    
    return report


if __name__ == "__main__":
    # Default to project directory
    if len(sys.argv) > 1:
        project_path = Path(sys.argv[1])
    else:
        project_path = Path(__file__).parent.parent
    
    run_quality_evaluation(project_path)
