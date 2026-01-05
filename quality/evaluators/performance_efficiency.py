"""
Performance Efficiency Evaluator - ISO/IEC 25010
------------------------------------------------
Measures: Time Behaviour, Resource Utilization, Capacity
Tools: psutil, time module
"""

import subprocess
import sys
import time
import os
import psutil
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class PerformanceResult:
    """Performance efficiency evaluation result."""
    import_time_ms: float      # Time to import main module
    memory_baseline_mb: float  # Memory at startup
    memory_peak_mb: float      # Peak memory during test
    cpu_utilization: float     # CPU usage percentage
    score: float
    details: Dict[str, Any]


def measure_import_time(project_dir: Path) -> Dict[str, Any]:
    """Measure time to import the main application module."""
    result = {
        "import_time_ms": 0.0,
        "modules_imported": 0,
        "error": None,
    }
    
    try:
        # Create a test script to measure import time
        test_script = f'''
import sys
import time
sys.path.insert(0, r"{project_dir / 'src'}")

start = time.perf_counter()
try:
    import app
    import_time = (time.perf_counter() - start) * 1000
    print(f"IMPORT_TIME={{import_time:.2f}}")
    print(f"MODULES={{len(sys.modules)}}")
except Exception as e:
    print(f"ERROR={{str(e)}}")
'''
        
        proc = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=60,
        )
        
        output = proc.stdout
        if "IMPORT_TIME=" in output:
            import_time_line = [l for l in output.split('\n') if 'IMPORT_TIME=' in l][0]
            result["import_time_ms"] = float(import_time_line.split('=')[1])
        
        if "MODULES=" in output:
            modules_line = [l for l in output.split('\n') if 'MODULES=' in l][0]
            result["modules_imported"] = int(modules_line.split('=')[1])
        
        if "ERROR=" in output:
            error_line = [l for l in output.split('\n') if 'ERROR=' in l][0]
            result["error"] = error_line.split('=', 1)[1]
        
    except subprocess.TimeoutExpired:
        result["error"] = "Import time measurement timed out"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def measure_memory_usage(project_dir: Path) -> Dict[str, Any]:
    """Measure memory usage of the application."""
    result = {
        "baseline_mb": 0.0,
        "peak_mb": 0.0,
        "python_overhead_mb": 0.0,
        "error": None,
    }
    
    try:
        # Measure Python baseline memory
        process = psutil.Process()
        result["python_overhead_mb"] = process.memory_info().rss / (1024 * 1024)
        
        # Create test script to measure memory
        test_script = f'''
import sys
import psutil
sys.path.insert(0, r"{project_dir / 'src'}")

process = psutil.Process()
baseline = process.memory_info().rss

try:
    import app
    peak = process.memory_info().rss
    
    print(f"BASELINE={{baseline / (1024*1024):.2f}}")
    print(f"PEAK={{peak / (1024*1024):.2f}}")
except Exception as e:
    print(f"ERROR={{str(e)}}")
'''
        
        proc = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=60,
        )
        
        output = proc.stdout
        if "BASELINE=" in output:
            line = [l for l in output.split('\n') if 'BASELINE=' in l][0]
            result["baseline_mb"] = float(line.split('=')[1])
        
        if "PEAK=" in output:
            line = [l for l in output.split('\n') if 'PEAK=' in l][0]
            result["peak_mb"] = float(line.split('=')[1])
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def measure_cpu_utilization() -> Dict[str, Any]:
    """Measure current CPU utilization."""
    result = {
        "cpu_percent": 0.0,
        "cpu_count": psutil.cpu_count(),
        "error": None,
    }
    
    try:
        # Get CPU usage over a 1 second interval
        result["cpu_percent"] = psutil.cpu_percent(interval=1)
    except Exception as e:
        result["error"] = str(e)
    
    return result


def evaluate(project_dir: Path) -> PerformanceResult:
    """
    Evaluate performance efficiency.
    
    Score calculation:
    - Import time: <500ms = 100, <1000ms = 80, <2000ms = 60, >2000ms = 40
    - Memory usage: <100MB = 100, <200MB = 80, <500MB = 60, >500MB = 40
    - Final score is average
    """
    # Run evaluations
    import_result = measure_import_time(project_dir)
    memory_result = measure_memory_usage(project_dir)
    cpu_result = measure_cpu_utilization()
    
    # Calculate import time score
    import_time = import_result.get("import_time_ms", 5000)
    if import_time < 500:
        import_score = 100
    elif import_time < 1000:
        import_score = 80
    elif import_time < 2000:
        import_score = 60
    else:
        import_score = 40
    
    # Calculate memory score
    peak_memory = memory_result.get("peak_mb", 1000)
    if peak_memory < 100:
        memory_score = 100
    elif peak_memory < 200:
        memory_score = 80
    elif peak_memory < 500:
        memory_score = 60
    else:
        memory_score = 40
    
    # Final score (equal weight)
    score = (import_score + memory_score) / 2
    
    return PerformanceResult(
        import_time_ms=import_time,
        memory_baseline_mb=memory_result.get("baseline_mb", 0),
        memory_peak_mb=peak_memory,
        cpu_utilization=cpu_result.get("cpu_percent", 0),
        score=score,
        details={
            "import": import_result,
            "memory": memory_result,
            "cpu": cpu_result,
            "import_score": import_score,
            "memory_score": memory_score,
        }
    )


if __name__ == "__main__":
    project_path = Path(__file__).parent.parent.parent
    result = evaluate(project_path)
    print(f"Performance Efficiency Score: {result.score:.1f}%")
    print(f"  Import Time: {result.import_time_ms:.0f}ms")
    print(f"  Peak Memory: {result.memory_peak_mb:.1f}MB")
