"""
ISO/IEC 25010 Quality Thresholds Configuration
----------------------------------------------
Defines pass/warning/fail thresholds for each quality characteristic.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Thresholds:
    """Threshold configuration for a quality characteristic."""
    pass_threshold: float  # >= this is PASS
    warn_threshold: float  # >= this is WARNING, < pass
    # < warn_threshold is FAIL


# Quality thresholds based on ISO/IEC 25010 recommendations
THRESHOLDS = {
    "functional_suitability": Thresholds(pass_threshold=80.0, warn_threshold=60.0),
    "performance_efficiency": Thresholds(pass_threshold=80.0, warn_threshold=60.0),
    "compatibility": Thresholds(pass_threshold=70.0, warn_threshold=50.0),
    "usability": Thresholds(pass_threshold=70.0, warn_threshold=50.0),
    "reliability": Thresholds(pass_threshold=85.0, warn_threshold=70.0),
    "security": Thresholds(pass_threshold=90.0, warn_threshold=75.0),
    "maintainability": Thresholds(pass_threshold=70.0, warn_threshold=50.0),
    "portability": Thresholds(pass_threshold=70.0, warn_threshold=50.0),
}

# Overall quality threshold
OVERALL_THRESHOLDS = Thresholds(pass_threshold=75.0, warn_threshold=60.0)

# Weight for each characteristic (all equal by default)
WEIGHTS = {
    "functional_suitability": 1.0,
    "performance_efficiency": 1.0,
    "compatibility": 1.0,
    "usability": 1.0,
    "reliability": 1.0,
    "security": 1.0,
    "maintainability": 1.0,
    "portability": 1.0,
}


def get_status(characteristic: str, score: float) -> str:
    """Get status (PASS/WARNING/FAIL) for a characteristic score."""
    threshold = THRESHOLDS.get(characteristic)
    if not threshold:
        return "UNKNOWN"
    
    if score >= threshold.pass_threshold:
        return "PASS"
    elif score >= threshold.warn_threshold:
        return "WARNING"
    else:
        return "FAIL"


def get_overall_status(score: float) -> str:
    """Get status for overall quality score."""
    if score >= OVERALL_THRESHOLDS.pass_threshold:
        return "PASS"
    elif score >= OVERALL_THRESHOLDS.warn_threshold:
        return "WARNING"
    else:
        return "FAIL"
