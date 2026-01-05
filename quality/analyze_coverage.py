"""Script to analyze current code coverage and identify gaps."""
import subprocess
import json
from pathlib import Path
import sys

# Fix encoding for Windows
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

def run_coverage():
    """Run coverage and parse results."""
    # Read coverage.json
    with open("coverage.json", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 60)
    print("COVERAGE GAP ANALYSIS")
    print("=" * 60)
    print(f"\nOverall Coverage: {data['totals']['percent_covered']:.1f}%")
    print(f"Lines Covered: {data['totals']['covered_lines']}")
    print(f"Lines Missing: {data['totals']['missing_lines']}")
    print("\n" + "-" * 60)
    print("FILES WITH MISSING COVERAGE (sorted by gap size):")
    print("-" * 60)
    
    gaps = []
    for file_path, file_data in data['files'].items():
        missing = file_data['missing_lines']
        if missing:
            gaps.append({
                'file': file_path,
                'coverage': file_data['summary']['percent_covered'],
                'missing_count': len(missing),
                'missing_lines': missing[:20],
                'total_missing': len(missing)
            })
    
    gaps.sort(key=lambda x: x['missing_count'], reverse=True)
    
    for gap in gaps:
        print(f"\n[{gap['file']}]")
        print(f"   Coverage: {gap['coverage']:.1f}% | Missing: {gap['missing_count']} lines")
        lines_preview = str(gap['missing_lines'][:10])
        if gap['total_missing'] > 10:
            lines_preview = lines_preview[:-1] + f", ... +{gap['total_missing']-10} more]"
        print(f"   Lines: {lines_preview}")

if __name__ == "__main__":
    run_coverage()
