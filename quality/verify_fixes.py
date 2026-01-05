import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quality.evaluators import (
    usability, 
    reliability, 
    maintainability, 
    portability,
    security, 
    compatibility, 
    performance_efficiency
)

def main():
    project_dir = project_root
    print(f"Verifying fixes for project: {project_dir}")
    
    evaluators = [
        ("Usability", usability.evaluate),
        ("Reliability", reliability.evaluate),
        ("Maintainability", maintainability.evaluate),
        ("Portability", portability.evaluate),
        ("Security", security.evaluate),
        ("Compatibility", compatibility.evaluate),
        ("Performance Efficiency", performance_efficiency.evaluate),
    ]

    scores = []
    
    for name, func in evaluators:
        print(f"\n[{name}]")
        try:
            res = func(project_dir)
            print(f"Score: {res.score:.1f}%")
            # print(f"Details: {res}")
            scores.append(res.score)
            
            # Specific checks
            if name == "Usability":
                print(f"  Docstring Coverage: {getattr(res, 'docstring_coverage', 'N/A')}%")
                print(f"  Error Handling Coverage: {getattr(res, 'error_handling_coverage', 'N/A')}%")
            elif name == "Reliability":
                print(f"  Exception Handling Ratio: {getattr(res, 'exception_handling_ratio', 'N/A')}%")
                print(f"  Resource Cleanup Ratio: {getattr(res, 'resource_cleanup_ratio', 'N/A')}%")
            elif name == "Portability":
                print(f"  Platform Specific Imports: {getattr(res, 'platform_specific_imports', 'N/A')}")
            elif name == "Maintainability":
                print(f"  Lint Score: {getattr(res, 'lint_score', 'N/A')}")

        except Exception as e:
            print(f"Error running {name}: {e}")
            scores.append(0.0)

    # Calculate average of these 7
    if scores:
        avg = sum(scores) / len(scores)
        print(f"\nAverage Score (excluding Functional Suitability): {avg:.1f}%")

if __name__ == "__main__":
    main()
